from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, AsyncGenerator, Awaitable, Callable, TypeAlias, Union

from nonebot_plugin_orm import get_scoped_session

from ..database.crud import UsageORM
from ..plugin.loader import _get_caller_plugin_name
from ._schema import ModelCompletions, ModelRequest, ModelStreamCompletions

if TYPE_CHECKING:
    from ._base import BaseLLM

ASK_FUNC: TypeAlias = Callable[..., Awaitable[Union[ModelCompletions, AsyncGenerator[ModelStreamCompletions, None]]]]


def record_plugin_usage(func: ASK_FUNC):
    """
    记录插件用量的装饰器
    """

    @wraps(func)
    async def wrapper(self: "BaseLLM", request: ModelRequest, *, stream: bool = False):
        plugin_name = _get_caller_plugin_name() or "muicebot"

        # Call the original 'ask' method
        response = await func(self, request, stream=stream)

        # Handle non-streaming response
        if isinstance(response, ModelCompletions):
            session = get_scoped_session()
            total_usage = response.usage if response.usage > 0 else 0
            await UsageORM.save_usage(session, plugin_name, total_usage)
            return response

        # Handle streaming response
        # elif isinstance(response, AsyncGenerator):
        async def generator_wrapper() -> AsyncGenerator[ModelStreamCompletions, None]:
            total_usage = 0
            try:
                async for chunk in response:
                    if not chunk.succeed:
                        continue

                    total_usage = chunk.usage if chunk.usage > 0 else 0
                    yield chunk
            finally:
                session = get_scoped_session()
                await UsageORM.save_usage(session, plugin_name, total_usage)

        return generator_wrapper()

    return wrapper
