from nonebot.adapters import Bot, Event

from muicebot.plugin import PluginMetadata
from muicebot.plugin.func_call import on_function_call
from muicebot.utils.adapters import ADAPTER_CLASSES

__metadata__ = PluginMetadata(
    name="muicebot-plugin-username", description="获取用户名的插件", usage="直接调用，返回当前对话的用户名"
)


@on_function_call(description="获取当前对话的用户名字")
async def get_username(bot: Bot, event: Event) -> str:
    userid = event.get_user_id()
    username = ""

    Onebotv12Bot = ADAPTER_CLASSES["onebot_v12"]
    Onebotv11Bot = ADAPTER_CLASSES["onebot_v11"]
    TelegramEvent = ADAPTER_CLASSES["telegram_event"]
    QQEvent = ADAPTER_CLASSES["qq_event"]

    if Onebotv12Bot and isinstance(bot, Onebotv12Bot):
        userinfo = await bot.get_user_info(user_id=userid)
        username = userinfo.get("user_displayname", userid)

    elif Onebotv11Bot and isinstance(bot, Onebotv11Bot):
        userinfo = await bot.get_stranger_info(user_id=int(userid))
        username = userinfo.get("nickname", userid)

    elif TelegramEvent and isinstance(event, TelegramEvent):
        username = event.chat.username  # type: ignore
        if not username:
            first_name = event.from_.first_name  # type: ignore
            last_name = event.from_.last_name  # type: ignore
            username = f"{first_name if first_name else ''} {last_name if last_name else ''}".strip()

    elif QQEvent and isinstance(event, QQEvent):
        username = event.member.nick  # type: ignore

    if not username:
        username = userid

    return username
