from arclet.alconna import Alconna
from nonebot.adapters import Event
from nonebot_plugin_alconna import (
    AlconnaMatch,
    Args,
    At,
    CommandMeta,
    Match,
    UniMessage,
    on_alconna,
)

from muicebot.plugin import PluginMetadata
from muicebot.utils.utils import get_username

__plugin_meta__ = PluginMetadata(
    name="muicebot_plugin_moechat", description="是优化群组聊天的插件", usage="/敲 @someone"
)

COMMAND_PREFIXES = ["/"]

command_poke = on_alconna(
    Alconna(COMMAND_PREFIXES, "敲", Args["target", At], meta=CommandMeta("敲某人", usage="/敲 @沐雪")),
    priority=50,
    block=True,
)

command_hug = on_alconna(
    Alconna(COMMAND_PREFIXES, "抱", Args["target", At], meta=CommandMeta("抱某人", usage="/抱 @沐雪")),
    priority=50,
    block=True,
)

command_stick = on_alconna(
    Alconna(COMMAND_PREFIXES, "贴", Args["target", At], meta=CommandMeta("和某人贴贴", usage="/贴 @沐雪")),
    priority=50,
    block=True,
)


@command_poke.handle()
async def poke(event: Event, target: Match[At] = AlconnaMatch("target")):
    user_id = event.get_user_id()
    user_name = await get_username(user_id, event)

    message = UniMessage(f"{user_name}敲了") + At(flag="user", target=target.result.target) + UniMessage("!")
    await command_poke.finish(message)


@command_hug.handle()
async def hug(event: Event, target: Match[At] = AlconnaMatch("target")):
    user_id = event.get_user_id()
    user_name = await get_username(user_id, event)

    message = UniMessage(f"{user_name}抱了抱") + At(flag="user", target=target.result.target) + UniMessage("!")
    await command_hug.finish(message)


@command_stick.handle()
async def stick(event: Event, target: Match[At] = AlconnaMatch("target")):
    user_id = event.get_user_id()
    user_name = await get_username(user_id, event)

    message = UniMessage(f"{user_name}和") + At(flag="user", target=target.result.target) + UniMessage("贴贴~")
    await command_stick.finish(message)
