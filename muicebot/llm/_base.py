from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Literal, Union, overload

from ._config import EmbeddingConfig, ModelConfig
from ._schema import (
    EmbeddingsBatchResult,
    ModelCompletions,
    ModelRequest,
    ModelStreamCompletions,
)


class BaseLLM(ABC):
    """
    模型基类，所有模型加载器都必须继承于该类

    推荐使用该基类中定义的方法构建模型加载器类，但无论如何都必须实现 `ask` 方法
    """

    def __init__(self, model_config: ModelConfig) -> None:
        """
        统一在此处声明变量
        """
        self.config = model_config
        """模型配置"""
        self.is_running = False
        """模型状态"""

    def _require(self, *require_fields: str):
        """
        通用校验方法：检查指定的配置项是否存在，不存在则抛出错误

        :param require_fields: 需要检查的字段名称（字符串）
        """
        missing_fields = [field for field in require_fields if not getattr(self.config, field, None)]
        if missing_fields:
            raise ValueError(f"对于 {self.config.provider} 以下配置是必需的: {', '.join(missing_fields)}")

    def _build_messages(self, request: "ModelRequest") -> list:
        """
        构建对话上下文历史的函数
        """
        raise NotImplementedError

    def load(self) -> bool:
        """
        加载模型（通常是耗时操作，在线模型如无需校验可直接返回 true）

        :return: 是否加载成功
        """
        self.is_running = True
        return True

    async def _ask_sync(
        self, messages: list, tools: Any, response_format: Any, total_tokens: int = 0
    ) -> "ModelCompletions":
        """
        同步模型调用
        """
        raise NotImplementedError

    def _ask_stream(
        self, messages: list, tools: Any, response_format: Any, total_tokens: int = 0
    ) -> AsyncGenerator["ModelStreamCompletions", None]:
        """
        流式输出
        """
        raise NotImplementedError

    @overload
    async def ask(self, request: "ModelRequest", *, stream: Literal[False] = False) -> "ModelCompletions": ...

    @overload
    async def ask(
        self, request: "ModelRequest", *, stream: Literal[True] = True
    ) -> AsyncGenerator["ModelStreamCompletions", None]: ...

    @abstractmethod
    async def ask(
        self, request: "ModelRequest", *, stream: bool = False
    ) -> Union["ModelCompletions", AsyncGenerator["ModelStreamCompletions", None]]:
        """
        模型交互询问

        :param request: 模型调用请求体
        :param stream: 是否开启流式对话

        :return: 模型输出体
        """
        pass


class EmbeddingModel(ABC):
    """
    嵌入模型基类，所有模型加载器都必须继承于该类

    推荐使用该基类中定义的方法构建模型加载器类，但无论如何都必须实现 `embed` 方法
    """

    def __init__(self, config: EmbeddingConfig):
        self.config = config

    def _require(self, *require_fields: str):
        """
        通用校验方法：检查指定的配置项是否存在，不存在则抛出错误

        :param require_fields: 需要检查的字段名称（字符串）
        """
        missing_fields = [field for field in require_fields if not getattr(self.config, field, None)]
        if missing_fields:
            raise ValueError(f"对于 {self.config.provider} 嵌入模型，以下配置是必需的: {', '.join(missing_fields)}")

    @abstractmethod
    async def embed(self, texts: list[str]) -> "EmbeddingsBatchResult":
        """
        查询文本嵌入
        """
        raise NotImplementedError
