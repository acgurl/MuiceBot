import logging
import os
from typing import (
    AsyncGenerator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

import torch
from nonebot import logger
from transformers import AutoConfig, AutoModel, AutoTokenizer

from ._types import BasicModel, ModelConfig


class Transformers(BasicModel):
    """
    使用 transformers方案加载, 适合通过 P-tuning V2 方式微调的模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_path")
        self.model_path = self.config.model_path
        self.pt_model_path = self.config.adapter_path
        self.stream = self.config.stream

    def load(self) -> bool:
        config = AutoConfig.from_pretrained(self.model_path, trust_remote_code=True, pre_seq_len=128)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)

        if torch.cuda.is_available():
            model = AutoModel.from_pretrained(self.model_path, config=config, trust_remote_code=True).cuda()
        else:
            logging.warning("未检测到GPU,将使用CPU进行推理")
            model = AutoModel.from_pretrained(self.model_path, config=config, trust_remote_code=True).float()

        if self.pt_model_path:
            prefix_state_dict = torch.load(os.path.join(self.pt_model_path, "pytorch_model.bin"), map_location="cpu")
            new_prefix_state_dict = {}
            for k, v in prefix_state_dict.items():
                if k.startswith("transformer.prefix_encoder."):
                    new_prefix_state_dict[k[len("transformer.prefix_encoder.") :]] = v
            model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
            model.transformer.prefix_encoder.float()

        self.model = model.eval()
        self.is_running = True

        return self.is_running

    async def _ask_sync(self, prompt: str, history: List[Tuple[str, str]]) -> str:
        response, _ = self.model.chat(self.tokenizer, prompt, history=history)
        return response

    async def _ask_stream(self, prompt: str, history: List[Tuple[str, str]]) -> AsyncGenerator[str, None]:
        try:
            # 检查模型是否支持流式输出
            size = 0
            if hasattr(self.model, "stream_chat"):
                for response_chunk, _ in self.model.stream_chat(self.tokenizer, prompt, history=history):
                    yield response_chunk[size:]
                    size = len(response_chunk)
            else:
                # 如果模型不支持流式输出，退回到非流式并一次性返回
                logger.warning("模型不支持流式输出，退回到非流式...")
                response, _ = self.model.chat(self.tokenizer, prompt, history=history)
                yield response
        except Exception as e:
            logging.error(f"流式输出发生错误: {e}")
            yield f"(模型处理错误: {str(e)})"

    @overload
    async def ask(self, prompt: str, history: List[Tuple[str, str]], stream: Literal[False]) -> str: ...

    @overload
    async def ask(
        self, prompt: str, history: List[Tuple[str, str]], stream: Literal[True]
    ) -> AsyncGenerator[str, None]: ...

    async def ask(
        self, prompt: str, history: list = [], stream: Optional[bool] = False
    ) -> Union[AsyncGenerator[str, None], str]:

        if not stream:
            return await self._ask_sync(prompt, history)

        return self._ask_stream(prompt, history)
