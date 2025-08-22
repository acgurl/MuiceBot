from typing import Any, Callable, Coroutine, TypeVar

SYNC_FUNCTION_CALL_FUNC = Callable[..., str]
ASYNC_FUNCTION_CALL_FUNC = Callable[..., Coroutine[str, Any, str]]
FUNCTION_CALL_FUNC = SYNC_FUNCTION_CALL_FUNC | ASYNC_FUNCTION_CALL_FUNC

F = TypeVar("F", bound=FUNCTION_CALL_FUNC)
