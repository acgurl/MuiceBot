from typing import AsyncGenerator, List, Literal, Optional, Tuple, Union, overload

import httpx
import openai
from nonebot import logger

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


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
        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.api_base)

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

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False,
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

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API 错误: {e}", exc_info=True)

        except httpx.RequestError as e:
            logger.error(f"请求失败: {e}", exc_info=True)

        return "（模型内部错误）"

    async def _ask_stream(self, prompt: str, history: List[Tuple[str, str]]) -> AsyncGenerator[str, None]:
        messages = self._build_messages(prompt, history)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
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

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API 错误: {e}", exc_info=True)
            yield f"OpenAI API 错误: {e}"
        except httpx.RequestError as e:
            logger.error(f"请求失败: {e}", exc_info=True)
            yield f"请求失败: {e}"

    @overload
    async def ask(self, prompt: str, history: List[Tuple[str, str]], stream: Literal[False]) -> str: ...

    @overload
    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Optional[bool] = False
    ) -> Union[AsyncGenerator[str, None], str]:
        """
        向 OpenAI 模型发送请求，并获取模型的推理结果

        :param prompt: 输入给模型的文本
        :param history: 之前的对话历史（可选）
        :return: 模型生成的文本
        """
        if stream:
            return self._ask_stream(prompt, history)
        return await self._ask_sync(prompt, history)
