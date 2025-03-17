from typing import AsyncGenerator, List, Literal, Optional, Union, overload

import ollama
from nonebot import logger
from ollama import ResponseError

from ..utils import get_image_base64
from ._types import BasicModel, Message, ModelConfig
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

    def __build_image_message(self, prompt: str, image_paths: List[str] = []) -> dict:
        images = []

        for image_path in image_paths:
            image_base64 = get_image_base64(local_path=image_path)
            images.append(image_base64)

        message = {"role": "user", "content": prompt, "images": images}

        return message

    def _build_messages(self, prompt: str, history: List[Message], image_paths: List[str] = []) -> list:
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        if self.auto_user_instructions:
            self.user_instructions = auto_system_prompt(prompt)

        for index, item in enumerate(history):
            if index == 0:
                user_content = self.user_instructions + "\n" + item.message
            else:
                user_content = item.message

            messages.append(self.__build_image_message(user_content, image_paths))
            messages.append({"role": "assistant", "content": item.respond})

        if not history and self.user_instructions:
            user_content = self.user_instructions + "\n" + prompt
        else:
            user_content = prompt

        message = self.__build_image_message(user_content, image_paths)

        messages.append(message)

        return messages

    async def _ask_sync(self, messages: list) -> str:
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

    async def _ask_stream(self, messages: list) -> AsyncGenerator[str, None]:
        try:
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

            async for chunk in response:
                logger.debug(chunk)

                if chunk.message.content:
                    yield chunk.message.content

        except Exception as e:
            logger.error(f"流式处理中断: {e}")
            yield f"(处理出错: {str(e)})"

    @overload
    async def ask(self, prompt: str, history: List[Message], stream: Literal[False]) -> str: ...

    @overload
    async def ask(self, prompt: str, history: List[Message], stream: Literal[True]) -> AsyncGenerator[str, None]: ...

    async def ask(
        self, prompt: str, history: List[Message], stream: Optional[bool] = False
    ) -> Union[AsyncGenerator[str, None], str]:
        messages = self._build_messages(prompt, history)

        if stream:
            return self._ask_stream(messages)
        return await self._ask_sync(messages)

    # 多模态实现
    @overload
    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Message], stream: Literal[False]
    ) -> str: ...

    @overload
    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Message], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask_vision(
        self, prompt, image_paths: List[str], history: List[Message], stream: bool = False
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
