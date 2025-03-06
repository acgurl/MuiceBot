import httpx
import openai
from nonebot import logger

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class Openai(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("api_key", "model_name")

    def load(self) -> bool:
        self.api_key = self.config.api_key
        self.model = self.config.model_name
        self.api_base = (
            self.config.api_host
            if self.config.api_host
            else "https://api.openai.com/v1"
        )
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.user_instructions = self.config.user_instructions
        self.auto_user_instructions = self.config.auto_user_instructions

        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.api_base)
        self.is_running = True
        return self.is_running

    async def ask(self, prompt, history=None) -> str:
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

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # 获取并返回模型生成的文本
            if self.model in ["deepseek-reasoner"]:
                return (
                    f"<think>{response.choices[0].message.reasoning_content}</think>"  # type: ignore
                    f"{response.choices[0].message.content}"
                )

            if response.choices[0].message.content:
                return response.choices[0].message.content

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API 错误: {e}", exc_info=True)
        except httpx.RequestError as e:
            logger.error(f"请求失败: {e}", exc_info=True)

        return "（模型内部错误）"
