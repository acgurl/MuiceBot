from typing import AsyncGenerator, List, Literal, Optional, Union, overload

import openai
from nonebot import logger

from ._types import BasicModel, Message, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt
from .utils.images import get_image_base64


class Openai(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("api_key", "model_name")
        self.api_key = self.config.api_key
        self.model = self.config.model_name
        self.api_base = self.config.api_host if self.config.api_host else "https://api.openai.com/v1"
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.user_instructions = self.config.user_instructions
        self.auto_user_instructions = self.config.auto_user_instructions
        self.stream = self.config.stream
        self.enable_search = self.config.online_search

        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.api_base, timeout=30)
        self.extra_body = {"enable_search": True} if self.enable_search else None

    def __build_image_message(self, prompt: str, image_paths: List[str]) -> dict:
        user_content: List[dict] = [{"type": "text", "text": prompt}]

        for url in image_paths:
            image_format = url.split(".")[-1]
            image_url = f"data:image/{image_format};base64,{get_image_base64(local_path=url)}"
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})

        return {"role": "user", "content": user_content}

    def _build_messages(self, prompt: str, history: List[Message], image_paths: Optional[List[str]] = []) -> list:
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        if self.auto_user_instructions:
            self.user_instructions = auto_system_prompt(prompt)

        if history:
            for index, item in enumerate(history):
                if index == 0:
                    user_msg = self.user_instructions + "\n" + item.message
                else:
                    user_msg = item.message

                user_content = (
                    {"role": "user", "content": user_msg}
                    if not item.images
                    else self.__build_image_message(item.message, item.images)
                )

                messages.append(user_content)
                messages.append({"role": "assistant", "content": item.respond})

        if not history and self.user_instructions:
            text = self.user_instructions + "\n" + prompt
        else:
            text = prompt

        user_content = (
            {"role": "user", "content": text} if not image_paths else self.__build_image_message(text, image_paths)
        )

        messages.append(user_content)

        return messages

    async def _ask_sync(self, messages: list, **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False,
                extra_body=self.extra_body,
            )

            result = ""
            message = response.choices[0].message  # type:ignore

            if (
                hasattr(message, "reasoning_content")  # type:ignore
                and message.reasoning_content  # type:ignore
            ):
                result += f"<think>{message.reasoning_content}</think>"  # type:ignore

            if message.content:  # type:ignore
                result += message.content  # type:ignore
            return result if result else "（警告：模型无输出！）"

        except openai.APIConnectionError as e:
            error_message = f"API 连接错误: {e}"
            logger.error(error_message)
            logger.error(e.__cause__)

        except openai.APIStatusError as e:
            error_message = f"API 状态异常: {e.status_code}({e.response})"
            logger.error(error_message)

        return error_message

    async def _ask_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
                extra_body=self.extra_body,
            )

            is_insert_think_label = False

            async for chunk in response:
                delta = chunk.choices[0].delta
                answer_content = delta.content

                if (
                    hasattr(delta, "reasoning_content") and delta.reasoning_content  # type:ignore
                ):
                    reasoning_content = chunk.choices[0].delta.reasoning_content  # type:ignore
                    yield (reasoning_content if is_insert_think_label else "<think>" + reasoning_content)
                    is_insert_think_label = True

                elif answer_content:
                    yield (answer_content if not is_insert_think_label else "</think>" + answer_content)
                    is_insert_think_label = False

        except openai.APIConnectionError as e:
            error_message = f"API 连接错误: {e}"
            logger.error(error_message)
            logger.error(e.__cause__)

        except openai.APIStatusError as e:
            error_message = f"API 状态异常: {e.status_code}({e.response})"
            logger.error(error_message)

        yield error_message

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
        多模态：图像识别

        :param image_path: 图像路径
        :return: 识别结果
        """
        messages = self._build_messages(prompt, history, images)

        if stream:
            return self._ask_stream(messages)

        return await self._ask_sync(messages)
