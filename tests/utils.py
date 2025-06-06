from time import time_ns

from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
from nonebot.adapters.onebot.v11.event import Sender

from .models import BotInfo


def ob11_private_message_event(
    message: str,
    self_id: int = BotInfo.self_id,
    user_id: int = BotInfo.superuser_id,
    message_id: int = BotInfo.message_id,
    to_me: bool = False,
) -> PrivateMessageEvent:
    return PrivateMessageEvent(
        time=time_ns(),
        self_id=self_id,
        post_type="message",
        sub_type="",
        user_id=user_id,
        message_type="private",
        message_id=message_id,
        message=Message(message),
        original_message=Message(message),
        raw_message=message,
        font=1,
        sender=Sender(user_id=user_id),
        to_me=to_me,
    )
