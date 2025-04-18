from nonebot.adapters import Bot, Event

from muicebot.plugin import PluginMetadata
from muicebot.plugin.func_call import on_function_call
from muicebot.utils.utils import get_username as get_username_

__metadata__ = PluginMetadata(
    name="muicebot-plugin-username", description="获取用户名的插件", usage="直接调用，返回当前对话的用户名"
)


@on_function_call(description="获取当前对话的用户名字")
async def get_username(bot: Bot, event: Event) -> str:
    user_id = event.get_user_id()
    return await get_username_(user_id)
