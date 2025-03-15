import os
from typing import AsyncGenerator, List, Literal, Optional, Tuple, Union, overload

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    ChatRequestMessage,
    ContentItem,
    ImageContentItem,
    ImageDetailLevel,
    ImageUrl,
    SystemMessage,
    TextContentItem,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from nonebot import logger

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class Azure(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name")
        self.model_name = self.config.model_name
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.user_instructions = self.config.user_instructions
        self.auto_user_instructions = self.config.auto_user_instructions
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.frequency_penalty = self.config.frequency_penalty
        self.presence_penalty = self.config.presence_penalty
        self.token = os.getenv("AZURE_API_KEY", self.config.api_key)
        self.endpoint = self.config.api_host if self.config.api_host else "https://models.inference.ai.azure.com"

    def _build_messages(
        self, prompt: str, history: List[Tuple[str, str]], image_paths: Optional[List] = None
    ) -> List[ChatRequestMessage]:
        messages: List[ChatRequestMessage] = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)

        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        for user_msg, assistant_msg in history:
            messages.append(UserMessage(user_msg))
            messages.append(AssistantMessage(assistant_msg))

        if self.auto_user_instructions:
            self.user_instructions = auto_system_prompt(prompt)

        if self.user_instructions and not history:
            user_message = self.user_instructions + "\n" + prompt
        else:
            user_message = prompt

        if not image_paths:
            messages.append(UserMessage(user_message))
            return messages

        image_content_items: List[ContentItem] = []

        for item in image_paths:
            image_content_items.append(
                ImageContentItem(
                    image_url=ImageUrl.load(
                        image_file=item, image_format=item.split(".")[-1], detail=ImageDetailLevel.AUTO
                    )
                )
            )

        content = [TextContentItem(text=user_message)] + image_content_items

        messages.append(UserMessage(content=content))

        return messages

    async def _ask_sync(self, messages: List[ChatRequestMessage]) -> str:
        client = ChatCompletionsClient(endpoint=self.endpoint, credential=AzureKeyCredential(self.token))

        try:
            response = await client.complete(
                messages=messages,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stream=False,
            )
            return response.choices[0].message.content  # type: ignore
        except Exception as e:
            logger.error(f"非流式 API 调用失败: {e}")
            return "模型响应失败"
        finally:
            await client.close()

    async def _ask_stream(self, messages: List[ChatRequestMessage]) -> AsyncGenerator[str, None]:
        client = ChatCompletionsClient(endpoint=self.endpoint, credential=AzureKeyCredential(self.token))

        try:
            response = await client.complete(
                messages=messages,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stream=True,  # 这里强制流式
            )

            async for chunk in response:
                if chunk.choices and chunk["choices"][0]["delta"]:
                    yield chunk["choices"][0]["delta"]["content"]

        except Exception as e:
            logger.error(f"流式处理中断: {e}")
        finally:
            await client.close()

    @overload
    async def ask(self, prompt: str, history: List[Tuple[str, str]], stream: Literal[False]) -> str: ...

    @overload
    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: bool = False
    ) -> Union[AsyncGenerator[str, None], str]:
        messages = self._build_messages(prompt, history)

        if stream:
            return self._ask_stream(messages)

        return await self._ask_sync(messages)

    # 多模态实现
    @overload
    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Tuple[str, str]], stream: Literal[False]
    ) -> str: ...

    @overload
    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Tuple[str, str]], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Tuple[str, str]], stream: bool = False
    ) -> Union[AsyncGenerator[str, None], str]:
        """
        多模态：图像识别

        :param image_paths: 图片路径列表
        :return: 图片描述
        """
        messages = self._build_messages(prompt, history, image_paths)

        if stream:
            return self._ask_stream(messages)

        return await self._ask_sync(messages)
