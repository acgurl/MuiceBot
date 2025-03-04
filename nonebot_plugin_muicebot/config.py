import os
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Dict

import yaml as yaml_
from nonebot import get_plugin_config
from pydantic import BaseModel, field_validator
from ruamel.yaml import YAML


class Config(BaseModel):
    model: Dict[str, Any] = {
        "loader": str,
    }
    """configs.yml 中的模型配置：计划对每个模型加载器引入设置模板"""

    muice_nicknames: list = []
    """沐雪的自定义昵称，作为消息前缀条件响应信息事件"""

    @field_validator("model")
    @classmethod
    def check_model_loader(cls, v) -> Dict[str, Any]:
        if not v.get("loader"):
            raise ValueError("loader is required")

        # Check if the specified loader exists
        loader_name = v["loader"]
        module_path = f"nonebot_plugin_muicebot.llm.{loader_name}"

        # 使用 find_spec 仅检测模块是否存在，不实际导入
        if find_spec(module_path) is None:
            raise ValueError(f"指定的模型加载器 '{v['loader']}' 不存在于 llm 目录中")

        return v

    class Config:
        extra = "allow"


# https://github.com/Moemu/Muice-Chatbot/blob/main/utils/configs.py

TEMPLATE_PATH = Path("configs.yml.example").resolve()
CONFIG_PATH = Path("configs.yml").resolve()
yaml = YAML()


# @update_config
def get() -> dict:
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError("configs.yml 不存在！请先创建")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = yaml_.load(f, Loader=yaml_.FullLoader)

    configs.update({"model.default": configs.get("model", {})})

    return configs


plugin_config = get_plugin_config(Config)

config = Config(**get())
