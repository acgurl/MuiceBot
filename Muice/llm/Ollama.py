from collections.abc import AsyncIterator
from typing import AsyncGenerator, Union

import ollama
from nonebot import logger
from ollama import ChatResponse

from ._types import BasicModel, ModelConfig


class Ollama(BasicModel):
    """
    使用 Ollama 模型服务调用模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name")

    def load(self) -> bool:
        self.model = self.config.model_name
        host = self.config.api_host if self.config.api_host else "http://localhost:11434"
        self.top_k = self.config.top_k
        self.top_p = self.config.top_p
        self.temperature = self.config.temperature
        self.repeat_penalty = self.config.repetition_penalty
        self.presence_penalty = self.config.presence_penalty
        self.frequency_penalty = self.config.frequency_penalty
        self.stream = self.config.stream

        self.client = ollama.AsyncClient(host=host)
        self.is_running = True
        return self.is_running

    async def ask(self, user_text: str, history: list) -> Union[AsyncGenerator[str, None], str]:
        messages = []
        if history:
            for chat in history:
                messages.append({"role": "user", "content": chat[0]})
                messages.append({"role": "assistant", "content": chat[1]})
        messages.append({"role": "user", "content": user_text})

        response = await self.client.chat(
            model=self.model,
            messages=messages,
            stream=self.stream,
            options={
                "temperature": self.temperature,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
            },
        )

        if isinstance(response, ChatResponse) and response.message.content:
            return response.message.content

        if isinstance(response, AsyncIterator):

            async def content_generator():
                try:
                    async for chunk in response:
                        logger.debug(chunk)
                        if chunk.message.content:
                            yield chunk.message.content
                except Exception as e:
                    logger.error(f"流式处理中断: {e}")

            return content_generator()

        return "(模型内部错误：未指定的类型)"
