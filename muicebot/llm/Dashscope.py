import asyncio
import json
import pathlib
from functools import partial
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
        self.stream = False
        self.succeed = True

    def __build_image_message(self, prompt: str, image_paths: List[str]) -> dict:
        image_contents = []
        for image_path in image_paths:
            if not (image_path.startswith("http") or image_path.startswith("file")):
                abs_path = pathlib.Path(image_path).resolve()
                image_path = abs_path.as_uri()
                image_path = image_path.replace("file:///", "file://")

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
                {"role": "user", "content": msg.message}
                if not msg.images
                else self.__build_image_message(msg.message, msg.images)
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

        if response.output.text:
            return response.output.text

        message_content = response.output.choices[0].message.content
        if message_content:
            return message_content if isinstance(message_content, str) else "".join(message_content)

        return await self._tool_calls_handle_sync(messages, response)

    async def _Generator_handle(
        self,
        messages: list,
        response: Generator[GenerationResponse, None, None] | Generator[MultiModalConversationResponse, None, None],
    ) -> AsyncGenerator[str, None]:
        is_insert_think_label = False
        is_function_call = False

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

            elif chunk.output.choices and chunk.output.choices[0].message.get("tool_calls", []):
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
                continue

            elif hasattr(chunk.output, "text") and chunk.output.text:  # 傻逼 Dashscope 为什么不统一接口？
                yield chunk.output.text
                continue

            elif chunk.output.choices is None:
                continue

            answer_content = chunk.output.choices[0].message.content
            reasoning_content = chunk.output.choices[0].message.get("reasoning_content", "")
            reasoning_content = reasoning_content.replace("\n</think>", "") if reasoning_content else ""
            # logger.debug(reasoning_content)

            if answer_content == "" and reasoning_content == "":
                continue

            elif reasoning_content != "" and answer_content == "":
                yield (reasoning_content if is_insert_think_label else "<think>" + reasoning_content)  # type:ignore
                is_insert_think_label = True

            elif answer_content != "":
                if isinstance(answer_content, list):
                    answer_content = answer_content[0].get("text") if answer_content else ""  # 现在知道了
                yield (answer_content if not is_insert_think_label else "</think>" + answer_content)
                is_insert_think_label = False

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
                    incremental_output=True,
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
                    incremental_output=True,
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
        self.stream = stream if stream is not None else False

        self._tools = tools if tools else []
        messages = self._build_messages(prompt, history, images, system)

        return await self._ask(messages)
