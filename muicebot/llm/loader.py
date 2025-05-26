import importlib

from ._base import BaseLLM
from ._config import ModelConfig
from .registry import get_llm_class


def load_model(config: ModelConfig) -> BaseLLM:
    """
    获得一个 LLM 实例
    """
    module_name = config.loader.lower()
    module_path = f"muicebot.llm.providers.{module_name}"

    # 延迟导入模型模块（只导一次）
    importlib.import_module(module_path)

    # 注册之后，直接取类使用
    LLMClass = get_llm_class(config.loader)

    return LLMClass(config)
