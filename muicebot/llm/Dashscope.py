import asyncio
import json
from functools import partial
from pathlib import Path
from typing import (
    AsyncGenerator,
    Generator,
    List,
    Literal,
    Optional,
    Union,
    overload,
)

import dashscope
from dashscope.api_entities.dashscope_response import (
    GenerationResponse,
    MultiModalConversationResponse,
)
from nonebot import logger

from ._types import BasicModel, Message, ModelConfig, function_call_handler


class Dashscope(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("api_key", "model_name")
        self.api_key = self.config.api_key
        self.model = self.config.model_name
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.repetition_penalty = self.config.repetition_penalty
        self.enable_search = self.config.online_search

        self._tools: List[dict] = []

        self.extra_headers = (
            {"X-DashScope-DataInspection": '{"input":"cip","output":"cip"}'} if self.config.content_security else {}
        )

        self.stream = False
        self.succeed = True

    def __build_image_message(self, prompt: str, image_paths: List[str]) -> dict:
        image_contents = []
        for image_path in image_paths:
            if not (image_path.startswith("http") or image_path.startswith("file:")):
                image_path = str(Path(image_path).resolve())

            image_contents.append({"image": image_path})

        user_content = [image_content for image_content in image_contents]

        if not prompt:
            prompt = "请描述图像内容"
        user_content.append({"type": "text", "text": prompt})

        return {"role": "user", "content": user_content}

    def _build_messages(
        self, prompt: str, history: List[Message], image_paths: Optional[List[str]] = None, system: Optional[str] = None
    ) -> list:
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        for msg in history:
            user_msg = (
                self.__build_image_message(msg.message, msg.images)
                if all((self.config.multimodal, msg.images))
                else {"role": "user", "content": msg.message}
            )
            messages.append(user_msg)
            messages.append({"role": "assistant", "content": msg.respond})

        user_msg = (
            {"role": "user", "content": prompt} if not image_paths else self.__build_image_message(prompt, image_paths)
        )

        messages.append(user_msg)

        return messages

    async def _GenerationResponse_handle(
        self, messages: list, response: GenerationResponse | MultiModalConversationResponse
    ) -> str:
        if response.status_code != 200:
            self.succeed = False
            logger.error(f"模型调用失败: {response.status_code}({response.code})")
            logger.error(f"{response.message}")
            return f"模型调用失败: {response.status_code}({response.code})"

        self.total_tokens += int(response.usage.total_tokens)

        if response.output.text:
            return response.output.text

        message_content = response.output.choices[0].message.content
        if message_content:
            return message_content if isinstance(message_content, str) else message_content[0].get("text")

        return await self._tool_calls_handle_sync(messages, response)

    async def _Generator_handle(
        self,
        messages: list,
        response: Generator[GenerationResponse, None, None] | Generator[MultiModalConversationResponse, None, None],
    ) -> AsyncGenerator[str, None]:
        is_insert_think_label = False
        is_function_call = False
        total_tokens: int = 0
        tool_call_id: str = ""
        function_name: str = ""
        function_args_delta: str = ""

        for chunk in response:
            logger.debug(chunk)

            if chunk.status_code != 200:
                logger.error(f"模型调用失败: {chunk.status_code}({chunk.code})")
                logger.error(f"{chunk.message}")
                yield f"模型调用失败: {chunk.status_code}({chunk.code})"
                self.succeed = False
                return

            total_tokens = chunk.usage.total_tokens

            # 优先判断是否是工具调用（OpenAI-style function calling）
            if chunk.output.choices and chunk.output.choices[0].message.get("tool_calls", []):
                tool_calls = chunk.output.choices[0].message.tool_calls
                tool_call = tool_calls[0]
                if tool_call.get("id", ""):
                    tool_call_id = tool_call["id"]
                if tool_call.get("function", {}).get("name", ""):
                    function_name = tool_call.get("function").get("name")
                function_arg = tool_call.get("function", {}).get("arguments", "")
                if function_arg and function_args_delta != function_arg:
                    function_args_delta += function_arg
                is_function_call = True
                # 工具调用也可能在输出文本之后发生

            # DashScope 的 text 模式（非标准接口）
            if hasattr(chunk.output, "text") and chunk.output.text:
                yield chunk.output.text
                continue

            if chunk.output.choices is None:
                continue

            choice = chunk.output.choices[0].message
            answer_content = choice.content
            reasoning_content = choice.get("reasoning_content", "")
            reasoning_content = reasoning_content.replace("\n</think>", "") if reasoning_content else ""

            # 处理模型可能输出的 reasoning（思考内容）
            if reasoning_content:
                if not is_insert_think_label:
                    yield f"<think>{reasoning_content}"
                    is_insert_think_label = True
                else:
                    yield reasoning_content

            # 处理模型输出的 answer（最终回复）
            if answer_content:
                if isinstance(answer_content, list):
                    answer_content = answer_content[0].get("text", "")
                if is_insert_think_label:
                    yield f"</think>{answer_content}"
                    is_insert_think_label = False
                else:
                    yield answer_content

        # 更新 token 消耗
        self.total_tokens += total_tokens

        # 流式处理工具调用响应
        if is_function_call:
            async for final_chunk in await self._tool_calls_handle_stream(
                messages, tool_call_id, function_name, function_args_delta
            ):
                yield final_chunk

    async def _tool_calls_handle_sync(
        self, messages: List, response: GenerationResponse | MultiModalConversationResponse
    ) -> str:
        tool_call = response.output.choices[0].message.tool_calls[0]
        tool_call_id = tool_call["id"]
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])

        logger.info(f"function call 请求 {function_name}, 参数: {function_args}")
        function_return = await function_call_handler(function_name, function_args)
        logger.success(f"Function call 成功，返回: {function_return}")

        messages.append(response.output.choices[0].message)
        messages.append({"role": "tool", "content": function_return, "tool_call_id": tool_call_id})

        return await self._ask(messages)  # type:ignore

    async def _tool_calls_handle_stream(
        self, messages: List, tool_call_id: str, function_name: str, function_args_delta: str
    ) -> AsyncGenerator[str, None]:
        function_args = json.loads(function_args_delta)

        logger.info(f"function call 请求 {function_name}, 参数: {function_args}")
        function_return = await function_call_handler(function_name, function_args)  # type:ignore
        logger.success(f"Function call 成功，返回: {function_return}")

        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "function": {
                            "arguments": function_args_delta,
                            "name": function_name,
                        },
                        "type": "function",
                        "index": 0,
                    }
                ],
            }
        )
        messages.append({"role": "tool", "content": function_return, "tool_call_id": tool_call_id})

        return await self._ask(messages)  # type:ignore

    async def _ask(self, messages: list) -> Union[AsyncGenerator[str, None], str]:
        loop = asyncio.get_event_loop()

        if not self.config.multimodal:
            response = await loop.run_in_executor(
                None,
                partial(
                    dashscope.Generation.call,
                    api_key=self.api_key,
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    repetition_penalty=self.repetition_penalty,
                    stream=self.stream,
                    tools=self._tools,
                    parallel_tool_calls=True,
                    enable_search=self.enable_search,
                    incremental_output=self.stream,  # 给他调成一样的：这个参数只支持流式调用时设置为True
                    headers=self.extra_headers,
                ),
            )
        else:
            response = await loop.run_in_executor(
                None,
                partial(
                    dashscope.MultiModalConversation.call,
                    api_key=self.api_key,
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    repetition_penalty=self.repetition_penalty,
                    stream=self.stream,
                    tools=self._tools,
                    parallel_tool_calls=True,
                    enable_search=self.enable_search,
                    incremental_output=self.stream,
                ),
            )

        if isinstance(response, GenerationResponse) or isinstance(response, MultiModalConversationResponse):
            return await self._GenerationResponse_handle(messages, response)
        return self._Generator_handle(messages, response)

    @overload
    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        tools: Optional[List[dict]] = [],
        stream: Literal[False] = False,
        system: Optional[str] = None,
        **kwargs,
    ) -> str: ...

    @overload
    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        tools: Optional[List[dict]] = [],
        stream: Literal[True] = True,
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        tools: Optional[List[dict]] = [],
        stream: Optional[bool] = False,
        system: Optional[str] = None,
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:
        """
        因为 Dashscope 对于多模态模型的接口不同，所以这里不能统一函数
        """
        self.succeed = True
        self.total_tokens = 0
        self.stream = stream if stream is not None else False

        self._tools = tools if tools else []
        messages = self._build_messages(prompt, history, images, system)

        return await self._ask(messages)
