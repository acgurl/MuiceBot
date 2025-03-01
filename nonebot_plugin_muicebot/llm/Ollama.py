import ollama
from .types import BasicModel

class Ollama(BasicModel):
    """
    使用 Ollama 模型服务调用模型
    """
    def load(self, model_config: dict) -> bool:
        self.model = model_config.get("model_path", "")
        host = model_config.get("host", 'http://localhost:11434')
        self.client = ollama.Client(host=host)
        self.is_running = True
        return self.is_running

    def ask(self, user_text: str, history: list) -> str:
        messages = []
        if history:
            for chat in history:
                messages.append({"role": "user", "content": chat[0]})
                messages.append({"role": "assistant", "content": chat[1]})
        messages.append({"role": "user", "content": user_text})
        response = self.client.chat(self.model, messages)
        if response.message.content:
            return response.message.content
        return '（模型内部错误）'