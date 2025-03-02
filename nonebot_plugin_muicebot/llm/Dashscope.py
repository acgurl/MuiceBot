import dashscope
from dashscope.api_entities.dashscope_response import GenerationResponse, MultiModalConversationResponse
import pathlib
from .utils.auto_system_prompt import auto_system_prompt
from .types import BasicModel
from typing import Generator
from nonebot import logger
from ..config import Config

class Dashscope(BasicModel):
    def load(self, config: dict) -> bool:
        self.api_key = config.get("api_key", "")
        self.model = config.get("model_name", "")
        self.max_tokens = config.get("max_tokens", 1024)
        self.temperature = config.get("temperature", 0.75)
        self.top_p = config.get("top_p", 0.95)
        self.repetition_penalty = config.get("repetition_penalty", 1.0)
        self.system_prompt = config.get("system_prompt", "")
        self.auto_system_prompt = config.get("auto_system_prompt", False)
        self.is_running = True
        return self.is_running

    def ask(self, prompt, history=None) -> str:
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
            repetition_penalty=self.repetition_penalty
        )

        if isinstance(response, Generator):
            response = next(response)

        if isinstance(response, GenerationResponse):
            return response.output.text
        
        logger.error(f"DashScope failed to generate response: {response}")

        return '（模型内部错误）'
    
    def ask_vision(self, prompt, image_paths: list, history=None) -> str:
        '''
        多模态：图像识别

        :param image_path: 图像路径
        :return: 识别结果
        '''
        messages = []

        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if self.system_prompt:
            messages.append({"role": "system", "content": [{"type": "text", "text": self.system_prompt}]})
            
        if history:
            for h in history:
                messages.append({"role": "user", "content": [{"type": "text", "text": h[0]}]})
                messages.append({"role": "assistant", "content": [{"type": "text", "text": h[1]}]})

        image_contents = []
        for image_path in image_paths:
            if not (image_path.startswith("http") or image_path.startswith("file")):
                abs_path = pathlib.Path(image_path).resolve()
                image_path = abs_path.as_uri()
                image_path = image_path.replace("file:///", "file://")

            image_contents.append({'image': image_path})

        user_content = [image_content for image_content in image_contents]

        if not prompt:
            prompt = '请描述图像内容'
        user_content.append({"type": "text", "text": prompt})

        messages.append({"role": "user", "content": user_content})

        response = dashscope.MultiModalConversation.call( # type: ignore
            api_key=self.api_key,
            model=self.model,
            messages=messages
        )

        if isinstance(response, Generator):
            response = next(response)

        if response.status_code != 200:
            logger.error(f"DashScope failed to generate response: {response}")
            return '（模型内部错误）'

        if isinstance(response, MultiModalConversationResponse):
            if type(response.output.choices[0].message.content) == str:
                return response.output.choices[0].message.content
            return response.output.choices[0].message.content[0]['text'] # type: ignore

        logger.error(f"DashScope failed to generate response: {response}")
        return '（模型内部错误）'