import os
from pathlib import Path
from typing import List, Literal, Optional

import yaml as yaml_
from nonebot import get_plugin_config
from pydantic import BaseModel

from .llm import ModelConfig


class PluginConfig(BaseModel):
    log_level: str = "INFO"
    """日志等级"""
    muice_nicknames: list = []
    """沐雪的自定义昵称，作为消息前缀条件响应信息事件"""
    telegram_proxy: str | None = None
    """telegram代理，这个配置项用于获取图片时使用"""


plugin_config = get_plugin_config(PluginConfig)


class Schedule(BaseModel):
    id: str
    """调度器 ID"""
    trigger: Literal["cron", "interval"]
    """调度器类别"""
    ask: Optional[str] = None
    """向大语言模型询问的信息"""
    say: Optional[str] = None
    """直接输出的信息"""
    args: dict[str, int]
    """调度器参数"""
    target: dict
    """指定发送信息的目标用户/群聊"""


class Config(BaseModel):
    model: ModelConfig
    """configs.yml 中的模型配置"""
    schedule: List[Schedule]
    """调度器配置列表"""

    muice_nicknames: list = plugin_config.muice_nicknames
    """沐雪的自定义昵称，作为消息前缀条件响应信息事件"""

    class Config:
        extra = "allow"


CONFIG_PATH = Path("configs.yml").resolve()


def get_config(model_config_name: str = "model") -> Config:
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError("configs.yml 不存在！请先创建")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = yaml_.load(f, Loader=yaml_.FullLoader)

    model_config = configs.get(model_config_name, {})
    schedule_configs = configs.get("schedule", [])

    if not model_config:
        raise ValueError(f"{model_config_name} 模型配置项不存在！")

    model_config = ModelConfig(**model_config)
    schedule_configs = [Schedule(**schedule_config) for schedule_config in schedule_configs]

    configs.update({"model": model_config})
    configs.update({"schedule": schedule_configs})

    config = Config(**configs)

    return config
