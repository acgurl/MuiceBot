import asyncio
from functools import partial

from llmtuner.chat import ChatModel

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class LLmtuner(BasicModel):
    """
    使用LLaMA-Factory方案加载, 适合通过其他微调方案微调的模型加载
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_path", "adapter_path", "template")

    def load(self) -> bool:
        model_name_or_path = self.config.model_path
        adapter_name_or_path = self.config.adapter_path
        template = self.config.template
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.max_tokens = self.config.max_tokens
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.model = ChatModel(
            dict(
                model_name_or_path=model_name_or_path,
                adapter_name_or_path=adapter_name_or_path,
                template=template,
            )
        )
        self.is_running = True
        return self.is_running

    def __ask(self, prompt: str, history: list):
        messages = []
        if self.auto_system_prompt:
            self.system_prompt = auto_system_prompt(prompt)
        if history:
            for chat in history:
                messages.append({"role": "user", "content": chat[0]})
                messages.append({"role": "assistant", "content": chat[1]})
        messages.append({"role": "user", "content": prompt})
        response = self.model.chat(
            messages,
            system=self.system_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        return response[0].response_text

    async def ask(self, prompt, history=None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self.__ask, prompt=prompt, history=history))
