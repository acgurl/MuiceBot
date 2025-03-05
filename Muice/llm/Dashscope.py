import asyncio
import pathlib
from functools import partial
from typing import Generator

import dashscope
from dashscope.api_entities.dashscope_response import (
    GenerationResponse,
    MultiModalConversationResponse,
)
from nonebot import logger

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class Dashscope(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("api_key", "model_name")

    def load(self) -> bool:
        self.api_key = self.config.api_key
        self.model = self.config.model_name
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.repetition_penalty = self.config.repetition_penalty
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.is_running = True
        return self.is_running

    def __ask(self, prompt, history=None) -> str:
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        if history:
            for h in history:
                messages.append({"role": "user", "content": h[0]})
                messages.append({"role": "assistant", "content": h[1]})
        messages.append({"role": "user", "content": prompt})

        response = dashscope.Generation.call(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
        )

        if isinstance(response, Generator):
            response = next(response)

        if isinstance(response, GenerationResponse):
            return response.output.text

        logger.error(f"DashScope failed to generate response: {response}")

        return "（模型内部错误）"

    async def ask(self, prompt, history=None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self.__ask, prompt=prompt, history=history)
        )

    def __ask_vision(self, prompt, image_paths: list, history=None) -> str:
        """
        多模态：图像识别

        :param image_path: 图像路径
        :return: 识别结果
        """
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}],
                }
            )

        if history:
            for h in history:
                messages.append(
                    {"role": "user", "content": [{"type": "text", "text": h[0]}]}
                )
                messages.append(
                    {"role": "assistant", "content": [{"type": "text", "text": h[1]}]}
                )

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

        messages.append({"role": "user", "content": user_content})

        response = dashscope.MultiModalConversation.call(  # type: ignore
            api_key=self.api_key, model=self.model, messages=messages
        )

        if isinstance(response, Generator):
            response = next(response)

        if response.status_code != 200:
            logger.error(f"DashScope failed to generate response: {response}")
            return "（模型内部错误）"

        if isinstance(response, MultiModalConversationResponse):
            if isinstance(response.output.choices[0].message.content, str):
                return response.output.choices[0].message.content
            return response.output.choices[0].message.content[0]["text"]  # type: ignore

        logger.error(f"DashScope failed to generate response: {response}")
        return "（模型内部错误）"

    async def ask_vision(self, prompt, image_paths: list, history=None) -> str:
        """异步版本的 ask_vision 方法"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self.__ask_vision,
                prompt=prompt,
                image_paths=image_paths,
                history=history,
            ),
        )
