import ollama

from ._types import BasicModel, ModelConfig


class Ollama(BasicModel):
    """
    使用 Ollama 模型服务调用模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name")

    def load(self) -> bool:
        self.model = self.config.model_name
        host = self.config.api_host if self.config.api_host else "http://localhost:11434"
        self.client = ollama.AsyncClient(host=host)
        self.is_running = True
        return self.is_running

    async def ask(self, user_text: str, history: list) -> str:
        messages = []
        if history:
            for chat in history:
                messages.append({"role": "user", "content": chat[0]})
                messages.append({"role": "assistant", "content": chat[1]})
        messages.append({"role": "user", "content": user_text})
        response = await self.client.chat(self.model, messages)
        if response.message.content:
            return response.message.content
        return "（模型内部错误）"
