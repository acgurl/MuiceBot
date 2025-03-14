import asyncio
import logging
import os
from functools import partial
from typing import AsyncGenerator, Generator, Union

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

    def load(self) -> bool:
        model_path = self.config.model_path
        pt_model_path = self.config.adapter_path
        config = AutoConfig.from_pretrained(model_path, trust_remote_code=True, pre_seq_len=128)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if torch.cuda.is_available():
            model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True).cuda()
        else:
            logging.warning("未检测到GPU,将使用CPU进行推理")
            model = AutoModel.from_pretrained(model_path, config=config, trust_remote_code=True).float()
        if pt_model_path:
            prefix_state_dict = torch.load(os.path.join(pt_model_path, "pytorch_model.bin"), map_location="cpu")
            new_prefix_state_dict = {}
            for k, v in prefix_state_dict.items():
                if k.startswith("transformer.prefix_encoder."):
                    new_prefix_state_dict[k[len("transformer.prefix_encoder.") :]] = v
            model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
            model.transformer.prefix_encoder.float()
        self.model = model.eval()
        self.is_running = True

        # 获取流式输出配置，默认为False
        self.stream = getattr(self.config, "stream", False)

        return self.is_running

    def __ask(self, user_text: str, history: list) -> Generator[str, None, None]:
        """
        同步版本的对话函数，支持流式和非流式输出
        """
        if not self.stream:
            # 非流式输出模式
            response, _ = self.model.chat(self.tokenizer, user_text, history=history)
            yield response
        else:
            # 流式输出模式
            try:
                # 检查模型是否支持流式输出
                size = 0
                if hasattr(self.model, "stream_chat"):
                    for response_chunk, _ in self.model.stream_chat(self.tokenizer, user_text, history=history):
                        yield response_chunk[size:]
                        size = len(response_chunk)
                else:
                    # 如果模型不支持流式输出，退回到非流式并一次性返回
                    logger.warning("模型不支持流式输出，退回到非流式...")
                    response, _ = self.model.chat(self.tokenizer, user_text, history=history)
                    yield response
            except Exception as e:
                logging.error(f"流式输出发生错误: {e}")
                # 发生错误时返回错误信息
                yield f"(模型处理错误: {str(e)})"

    async def ask(self, user_text: str, history: list = []) -> Union[AsyncGenerator[str, None], str]:
        """
        异步版本的对话函数，根据stream参数返回字符串或异步生成器
        """
        if history is None:
            history = []

        loop = asyncio.get_event_loop()

        if not self.stream:
            generator = await loop.run_in_executor(None, partial(self.__ask, user_text=user_text, history=history))
            return "".join(generator)

        async def sync_to_async_generator():
            generator = await loop.run_in_executor(None, partial(self.__ask, user_text=user_text, history=history))

            for chunk in generator:
                yield chunk

        return sync_to_async_generator()
