from nonebot import require

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")

from nonebot.plugin import PluginMetadata  # noqa: E402

from .config import Config  # noqa: E402
from .onebot import *  # noqa: E402, F403, F401

__plugin_meta__ = PluginMetadata(
    name="MuiceAI Plugin",
    description="沐雪，一个不会自动找你聊天的AI女孩子",
    usage="瞎几把用",
    type="application",
    config=Config,
    homepage="https://bot.snowy.moe/",
    extra={},
)
