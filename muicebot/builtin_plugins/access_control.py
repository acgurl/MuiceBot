from nonebot import get_plugin_config, logger
from nonebot.adapters import Bot, Event
from nonebot.exception import IgnoredException
from nonebot.message import run_preprocessor
from nonebot_plugin_session import SessionIdType, extract_session
from pydantic import BaseModel

from muicebot.plugin import PluginMetadata


class ScopeConfig(BaseModel):
    blacklist: list[str] = []
    whitelist: list[str] = []


class Config(BaseModel):
    access_control: ScopeConfig = ScopeConfig()


__metadata__ = PluginMetadata(
    name="blacklist_whitelist_checker",
    description="黑白名单检测",
    usage="在插件配置中填写响应配置后即可",
    config=Config,
)

plugin_config = get_plugin_config(Config).access_control  # 获取插件配置

_BLACKLIST = plugin_config.blacklist
_WHITELIST = plugin_config.whitelist
_MODE = "white" if _WHITELIST else "black"


@run_preprocessor
async def access_control(bot: Bot, event: Event):
    session = extract_session(bot, event)
    group_id = session.get_id(SessionIdType.GROUP)
    user_id = session.get_id(SessionIdType.USER)
    level = session.level

    if _MODE == "black":
        if user_id in _BLACKLIST:
            msg = f"User {user_id} is in the blacklist"
            logger.warning(msg)
            raise IgnoredException(msg)

        elif group_id in _BLACKLIST:
            msg = f"Group {group_id} is in the blacklist"
            logger.warning(msg)
            raise IgnoredException(msg)

    if _MODE == "white":
        if level >= 2 and group_id not in _WHITELIST:  # 白名单只对群组生效
            msg = f"Group {group_id} is not in the whitelist"
            logger.warning(msg)
            raise IgnoredException(msg)
