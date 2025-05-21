from typing import Any

from muicebot.plugin.func_call import get_function_calls
from muicebot.plugin.mcp import handle_mcp_tool


async def function_call_handler(func: str, arguments: dict[str, str] | None = None) -> Any:
    """
    模型 Function Call 请求处理
    """
    arguments = arguments if arguments and arguments != {"dummy_param": ""} else {}

    if func_caller := get_function_calls().get(func):
        return await func_caller.run(**arguments)

    if mcp_result := await handle_mcp_tool(func, arguments):
        return mcp_result

    return "(Unknown Function)"
