import os
from typing import AsyncGenerator, List, Union

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    AsyncStreamingChatCompletions,
    ChatRequestMessage,
    SystemMessage,
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

    def load(self) -> bool:
        self.model_name = self.config.model_name
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.user_instructions = self.config.user_instructions
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.frequency_penalty = self.config.frequency_penalty
        self.presence_penalty = self.config.presence_penalty
        self.stream = self.config.stream
        try:
            self.token = os.environ["GITHUB_TOKEN"]
        except KeyError:
            self.token = self.config.api_key
        self.endpoint = (
            self.config.api_host
            if self.config.api_host
            else "https://models.inference.ai.azure.com"
        )
        self.is_running = True
        return self.is_running

    async def ask(
        self, prompt: str, history: list
    ) -> Union[AsyncGenerator[str, None], str]:
        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)

        messages: List[ChatRequestMessage] = []

        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        for h in history:
            messages.append(UserMessage(h[0]))
            messages.append(AssistantMessage(h[1]))

        if self.user_instructions and len(history) == 0:
            messages.append(UserMessage(self.user_instructions + "\n" + prompt))
        else:
            messages.append(UserMessage(prompt))

        client = ChatCompletionsClient(
            endpoint=self.endpoint, credential=AzureKeyCredential(self.token)
        )

        response = await client.complete(
            messages=messages,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stream=self.stream,
        )

        if isinstance(response, AsyncStreamingChatCompletions) and self.stream:

            async def content_generator():
                try:
                    async for chunk in response:
                        logger.debug(chunk)
                        if chunk.choices and chunk["choices"][0]["delta"]:
                            result = chunk["choices"][0]["delta"]["content"]
                            yield result
                except Exception as e:
                    logger.error(f"流式处理中断: {e}")
                finally:
                    await client.close()

            return content_generator()
        else:
            await client.close()
            return response.choices[0].message.content  # type: ignore
