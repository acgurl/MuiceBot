import os
from typing import List

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    ChatRequestMessage,
    SystemMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential

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

    async def ask(self, user_text: str, history: list):
        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(user_text)

        messages: List[ChatRequestMessage] = []

        if self.system_prompt:
            messages.append(SystemMessage(self.system_prompt))

        for h in history:
            messages.append(UserMessage(h[0]))
            messages.append(AssistantMessage(h[1]))

        if self.user_instructions and len(history) == 0:
            messages.append(UserMessage(self.user_instructions + "\n" + user_text))
        else:
            messages.append(UserMessage(user_text))

        async with ChatCompletionsClient(
            endpoint=self.endpoint, credential=AzureKeyCredential(self.token)
        ) as client:
            response = await client.complete(
                messages=messages,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
            )
        response_content = response.choices[0].message.content

        return response_content
