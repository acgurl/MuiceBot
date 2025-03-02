from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional
import yaml as yaml_
from importlib.util import find_spec
from pathlib import Path
from ruamel.yaml import YAML
from nonebot import logger, get_plugin_config

class Config(BaseModel, extra='allow'):
    # 模型配置
    model: Dict[str, Any] = {
        'loader':str,
    }

    @field_validator('model')
    @classmethod
    def check_model_loader(cls, v) -> Dict[str, Any]:
        if not v.get('loader'):
            raise ValueError('loader is required')
        
        # Check if the specified loader exists
        loader_name = v['loader']
        module_path = f"nonebot_plugin_muicebot.llm.{loader_name}"

        # 使用 find_spec 仅检测模块是否存在，不实际导入
        if find_spec(module_path) is None:
            raise ValueError(f"指定的模型加载器 '{v['loader']}' 不存在于 llm 目录中")
               
        return v

    # 适配器特定配置
    adapter_configs: Dict[str, Dict[str, Any]] = {}
    
    # 启用的适配器列表，空列表表示全部启用
    enabled_adapters: list[str] = []
    
    # 是否启用详细日志
    debug_mode: bool = False
    
    # 消息处理超时（秒）
    message_timeout: int = 30
    
    # 错误时的默认回复
    error_response: str = "处理消息时出现错误，请稍后再试。"


# https://github.com/Moemu/Muice-Chatbot/blob/main/utils/configs.py

TEMPLATE_PATH = Path("configs.yml.example").resolve()
CONFIG_PATH = Path("configs.yml").resolve()
yaml = YAML()

# @update_config
def get() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = yaml_.load(f, Loader=yaml_.FullLoader)

    configs.update({'model.default':configs.get('model',{})})

    return configs

config = Config(**get())