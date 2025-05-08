import inspect
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .func_call._types import ASYNC_FUNCTION_CALL_FUNC, SYNC_FUNCTION_CALL_FUNC


def path_to_module_name(module_path: Path, base_path: Path) -> str:
    """
    动态计算模块名，基于明确的基准路径
    """
    try:
        rel_path = module_path.resolve().relative_to(base_path.resolve())
    except ValueError:
        # 处理绝对路径与相对路径的兼容性问题
        rel_path = module_path.resolve()

    if rel_path.stem == "__init__":
        parts = rel_path.parts[:-1]
    else:
        parts = rel_path.parts

    # 过滤空字符串和无效部分
    module_names = [p for p in parts if p not in ("", ".", "..")]
    return ".".join(module_names)


def is_coroutine_callable(call: Callable[..., Any]) -> bool:
    """
    检查 call 是否是一个 callable 协程函数
    """
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    func_ = getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(func_)


def async_wrap(func: SYNC_FUNCTION_CALL_FUNC) -> ASYNC_FUNCTION_CALL_FUNC:
    """
    装饰器，将同步函数包装为异步函数
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper
