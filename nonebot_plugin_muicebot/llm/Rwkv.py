import aiohttp

from ._types import BasicModel, ModelConfig


class RWKV(BasicModel):
    """
    通过RWKV-RUNNER的api服务, 使用第三方RWKV模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name")

    def load(self) -> bool:
        self.model = self.config.model_name
        self.host = (
            self.config.api_host if self.config.api_host else "http://localhost:8000"
        )
        self.temperature = self.config.temperature
        self.top_p = self.config.top_p
        self.max_tokens = self.config.max_tokens
        self.presence_penalty = self.config.presence_penalty
        self.is_running = True
        return self.is_running

    async def ask(
        self,
        user_text: str,
        history: list,
    ):
        messages = []
        if history:
            for chat in history:
                messages.append({"role": "user", "content": chat[0], "raw": False})
                messages.append({"role": "assistant", "content": chat[1], "raw": False})

        messages.append({"role": "user", "content": user_text, "raw": False})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.host,
                json={
                    "frequency_penalty": self.presence_penalty,
                    "max_tokens": self.max_tokens,
                    "messages": messages,
                    "model": self.model,
                    "presence_penalty": self.presence_penalty,
                    "presystem": True,
                    "stream": False,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                },
            ) as response:
                json_data = await response.json()

        if "choices" in json_data and len(json_data["choices"]) > 0:
            return json_data["choices"][0]["message"]["content"].lstrip()
        # Handle the case when the expected structure is not present
        return "Error: Unexpected response format from RWKV API"
