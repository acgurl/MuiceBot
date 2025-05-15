from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    store_index: str = "https://raw.githubusercontent.com/MuikaAI/Muicebot-Plugins-Index/refs/heads/main/plugins.json"
    """插件索引文件 url"""


config = get_plugin_config(Config)
