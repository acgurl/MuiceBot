from typing import AsyncGenerator, List, Literal, Optional, Tuple, Union, overload

import ollama
from nonebot import logger
from ollama import ResponseError

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class Ollama(BasicModel):
    """
    使用 Ollama 模型服务调用模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name")
        self.model = self.config.model_name
        self.host = self.config.api_host if self.config.api_host else "http://localhost:11434"
        self.top_k = self.config.top_k
        self.top_p = self.config.top_p
        self.temperature = self.config.temperature
        self.repeat_penalty = self.config.repetition_penalty
        self.presence_penalty = self.config.presence_penalty
        self.frequency_penalty = self.config.frequency_penalty
        self.stream = self.config.stream

        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.user_instructions = self.config.user_instructions
        self.auto_user_instructions = self.config.auto_user_instructions

    def load(self) -> bool:
        try:
            self.client = ollama.AsyncClient(host=self.host)
            self.is_running = True
        except ResponseError as e:
            logger.error(f"加载 Ollama 加载器时发生错误： {e}")
        except ConnectionError as e:
            logger.error(f"加载 Ollama 加载器时发生错误： {e}")
        finally:
            return self.is_running

    def _build_messages(self, prompt: str, history: List[Tuple[str, str]]) -> list:
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
                    messages.append(
                        {
                            "role": "user",
                            "content": self.user_instructions + "\n" + item[0],
                        }
                    )
                else:
                    messages.append({"role": "user", "content": item[0]})
                messages.append({"role": "assistant", "content": item[1]})

        if not history and self.user_instructions:
            messages.append({"role": "user", "content": self.user_instructions + "\n" + prompt})
        else:
            messages.append({"role": "user", "content": prompt})

        return messages

    async def _ask_sync(self, prompt: str, history: List[Tuple[str, str]]) -> str:
        messages = self._build_messages(prompt, history)

        response = await self.client.chat(
            model=self.model,
            messages=messages,
            stream=False,
            options={
                "temperature": self.temperature,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
            },
        )

        return response.message.content if response.message.content else "(警告：模型无返回)"

    async def _ask_stream(self, prompt: str, history: List[Tuple[str, str]]) -> AsyncGenerator[str, None]:
        messages = self._build_messages(prompt, history)

        response = await self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
            },
        )

        try:
            async for chunk in response:
                logger.debug(chunk)
                if chunk.message.content:
                    yield chunk.message.content
        except Exception as e:
            logger.error(f"流式处理中断: {e}")

    @overload
    async def ask(self, prompt: str, history: List[Tuple[str, str]], stream: Literal[False]) -> str: ...

    @overload
    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Optional[bool] = False
    ) -> Union[AsyncGenerator[str, None], str]:
        if stream:
            return self._ask_stream(prompt, history)
        return await self._ask_sync(prompt, history)
