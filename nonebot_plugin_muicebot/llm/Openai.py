import openai
import requests
from nonebot import logger

from .types import BasicModel
from .utils.auto_system_prompt import auto_system_prompt


class Openai(BasicModel):
    def load(self, config: dict) -> bool:
        self.api_key = config.get("api_key")
        self.api_base = config.get(
            "api_base", "https://api.openai.com/v1"
        )  # 默认的 OpenAI API 基地址
        self.model = config.get("model_name", "text-davinci-003")
        self.max_tokens = config.get("max_tokens", 1024)
        self.temperature = config.get("temperature", 0.7)
        self.system_prompt = config.get("system_prompt", None)
        self.auto_system_prompt = config.get("auto_system_prompt", False)
        self.user_instructions = config.get("user_instructions", None)
        self.auto_user_instructions = config.get("auto_user_instructions", False)

        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
        self.is_running = True
        return self.is_running

    def ask(self, prompt, history=None) -> str:
        """
        向 OpenAI 模型发送请求，并获取模型的推理结果

        :param prompt: 输入给模型的文本
        :param history: 之前的对话历史（可选）
        :return: 模型生成的文本
        """
        try:
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
                messages.append(
                    {"role": "user", "content": self.user_instructions + "\n" + prompt}
                )
            else:
                messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # 获取并返回模型生成的文本
            if self.model in ["deepseek-reasoner"]:
                return "<think>" + response.choices[0].message.reasoning_content + "</think>" + response.choices[0].message.content  # type: ignore

            if response.choices[0].message.content:
                return response.choices[0].message.content

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API 错误: {e}", exc_info=True)
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}", exc_info=True)

        return "（模型内部错误）"
