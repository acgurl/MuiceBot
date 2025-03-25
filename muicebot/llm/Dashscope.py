import asyncio
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

from ._types import BasicModel, Message, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


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
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.enable_search = self.config.online_search

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

    def _build_messages(self, prompt: str, history: List[Message], image_paths: Optional[List[str]] = None) -> list:
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

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

    async def _ask_sync(self, messages: list) -> str:
        loop = asyncio.get_event_loop()

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
                stream=False,
                enable_search=self.enable_search,
            ),
        )

        if not isinstance(response, GenerationResponse):
            return "(模型内部错误：在流关闭的情况下返回了 Generator)"

        if response.status_code != 200:
            logger.error(f"模型调用失败: {response.status_code}({response.code})")
            logger.error(f"{response.message}")
            return f"模型调用失败: {response.status_code}({response.code})"

        return response.output.text

    async def _ask_stream(self, messages: list) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()

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
                stream=True,
                enable_search=self.enable_search,
            ),
        )

        if isinstance(response, GenerationResponse):
            logger.warning("模型内部错误：在流开启的情况下返回了 GenerationResponse")
            yield response.output.text
            return

        is_insert_think_label = False
        size = 0

        for chunk in response:
            if chunk.status_code != 200:
                logger.error(f"模型调用失败: {chunk.status_code}({chunk.code})")
                logger.error(f"{chunk.message}")
                yield f"模型调用失败: {chunk.status_code}({chunk.code})"

            if hasattr(chunk.output, "text") and chunk.output.text:  # 傻逼 Dashscope 为什么不统一接口？
                yield chunk.output.text[size:]
                size = len(chunk.output.text)
                continue

            answer_content = chunk.output.choices[0].message.content
            reasoning_content = chunk.output.choices[0].message.reasoning_content
            if answer_content == "" and reasoning_content == "":
                continue

            if reasoning_content != "" and answer_content == "":
                yield (reasoning_content if is_insert_think_label else "<think>" + reasoning_content)
                is_insert_think_label = True

            elif answer_content != "":
                if isinstance(answer_content, list):
                    answer_content = "".join(answer_content)  # 不知道为什么会是list
                yield (answer_content if not is_insert_think_label else "</think>" + answer_content)
                is_insert_think_label = False

    async def _ask_vision_sync(self, messages: list) -> str:
        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            partial(
                dashscope.MultiModalConversation.call,
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                stream=False,
            ),
        )

        if isinstance(response, Generator):
            return "(模型内部错误: 在流关闭的情况下返回了 Generator)"

        if response.status_code != 200:
            logger.error(f"模型调用失败: {response.status_code}({response.code})")
            logger.error(f"{response.message}")
            return f"模型调用失败: {response.status_code}({response.code})"

        if isinstance(response.output.choices[0].message.content, str):
            return response.output.choices[0].message.content

        return response.output.choices[0].message.content[0]["text"]  # type: ignore

    async def _ask_vision_stream(self, messages: list) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            partial(
                dashscope.MultiModalConversation.call,
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                stream=True,
            ),
        )

        if isinstance(response, MultiModalConversationResponse):
            logger.warning("模型内部错误：在流开启的情况下返回了 MultiModalConversationResponse")
            if isinstance(response.output.choices[0].message.content, str):
                yield response.output.choices[0].message.content
            else:
                yield response.output.choices[0].message.content[0]["text"]
            return

        size = 0

        for chunk in response:
            logger.debug(chunk)
            if chunk.status_code != 200:
                logger.error(f"模型调用失败: {chunk.status_code}({chunk.code})")
                logger.error(f"{chunk.message}")
                yield f"模型调用失败: {chunk.status_code}({chunk.code})"
                return

            content_body = chunk.output.choices[0].message.content
            if isinstance(content_body, str):
                yield content_body[size:]
                size = len(content_body)
            else:
                yield content_body[0]["text"][size:]
                size = len(content_body[0]["text"])

    @overload
    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        stream: Literal[False] = False,
        **kwargs,
    ) -> str: ...

    @overload
    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        stream: Literal[True] = True,
        **kwargs,
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self,
        prompt: str,
        history: List[Message],
        images: Optional[List[str]] = [],
        stream: Optional[bool] = False,
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:
        """
        因为 Dashscope 对于多模态模型的接口不同，所以这里不能统一函数
        """
        messages = self._build_messages(prompt, history, images)

        if stream:
            if self.config.multimodal:
                return self._ask_vision_stream(messages)
            return self._ask_stream(messages)

        if self.config.multimodal:
            return await self._ask_vision_sync(messages)
        return await self._ask_sync(messages)
