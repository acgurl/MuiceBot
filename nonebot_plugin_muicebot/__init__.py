from nonebot import require

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")

from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .config import Config
from .onebot import *

__plugin_meta__ = PluginMetadata(
    name="MuiceAI Plugin",
    description="沐雪，一个不会自动找你聊天的AI女孩子",
    usage="瞎几把用",
    type="application",
    config=Config,
    homepage="ai.snowy.moe/404.html",
    extra={},
)
