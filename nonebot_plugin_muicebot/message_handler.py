import traceback
from typing import Any, Callable, Dict, Optional, Type, Union

from nonebot import logger
from nonebot.adapters import Bot, Event, Message


class MessageHandler:
    """处理不同适配器的消息转换和交互"""

    _handlers: Dict[str, Callable] = {}
    _default_handler: Optional[Callable] = None

    @classmethod
    def register_adapter(cls, adapter_name: str):
        """装饰器：注册适配器的消息处理函数"""

        def decorator(func: Callable):
            cls._handlers[adapter_name] = func
            return func

        return decorator

    @classmethod
    def register_default(cls):
        """装饰器：注册默认消息处理函数"""

        def decorator(func: Callable):
            cls._default_handler = func
            return func

        return decorator

    @classmethod
    async def handle_response(
        cls, bot: Bot, event: Event, response: str
    ) -> Union[Message, str]:
        """根据不同的适配器处理响应"""
        adapter_name = bot.adapter.get_name()

        try:
            # 尝试使用注册的处理器
            if adapter_name in cls._handlers:
                return await cls._handlers[adapter_name](bot, event, response)

            # 尝试使用默认处理器
            if cls._default_handler:
                return await cls._default_handler(bot, event, response)

            # 如果没有处理器，返回原始字符串
            return response

        except Exception as e:
            logger.error(f"处理响应时出错 [{adapter_name}]: {e}")
            logger.debug(traceback.format_exc())
            return f"处理消息时出错: {e}"


# 为常见适配器注册处理函数


@MessageHandler.register_adapter("OneBot V11")
async def handle_onebot_v11(bot: Bot, event: Event, response: str) -> Message:
    from nonebot.adapters.onebot.v11 import Message as OnebotV11Message

    return OnebotV11Message(response)


@MessageHandler.register_adapter("OneBot V12")
async def handle_onebot_v12(bot: Bot, event: Event, response: str) -> Message:
    from nonebot.adapters.onebot.v12 import Message as OnebotV12Message

    return OnebotV12Message(response)


@MessageHandler.register_default()
async def handle_default(bot: Bot, event: Event, response: str) -> str:
    # 默认情况下返回原始字符串
    return response
