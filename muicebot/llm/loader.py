import importlib
from importlib.util import find_spec

from nonebot import logger

from ._base import BaseLLM
from ._config import ModelConfig
from .registry import get_llm_class


def load_model(config: ModelConfig) -> BaseLLM:
    """
    获得一个 LLM 实例
    """
    provider = config.provider.lower()

    # 如果是内置模型提供者，需要先导入
    # 否则视为已导入的插件
    builtin_provider = f"muicebot.llm.providers.{provider}"
    if find_spec(builtin_provider) is not None:
        logger.debug(f"加载内嵌模型模块: {provider}...")
        importlib.import_module(builtin_provider)

    # 注册之后，直接取类使用
    LLMClass = get_llm_class(provider)

    return LLMClass(config)
