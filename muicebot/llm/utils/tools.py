from typing import Any, Callable, Optional

from nonebot import logger

from muicebot.plugin.func_call import get_function_calls
from muicebot.plugin.mcp import handle_mcp_tool


async def function_call_handler(
    func: str, arguments: dict[str, str] | None = None, agent_handler: Optional[Callable[[str, str], Any]] = None
) -> Any:
    """
    模型 Function Call 请求处理

    Args:
        func: 工具名称
        arguments: 工具参数
        agent_handler: Agent工具处理函数，签名为 async def handler(agent_name: str, task: str) -> Any
    """
    arguments = arguments if arguments and arguments != {"dummy_param": ""} else {}

    # 检查是否为Agent工具调用
    if func.startswith("agent_"):
        agent_name = func[6:]  # 移除"agent_"前缀
        task = arguments.get("task", "") if arguments else ""
        if agent_name and task:
            # 优先使用传入的agent_handler
            if agent_handler:
                try:
                    result = await agent_handler(agent_name, task)
                    logger.success(f"Agent {agent_name} 执行成功，返回: {result}")
                    return result
                except Exception as e:
                    logger.error(f"Agent处理失败: {e}")
                    return f"Agent处理失败: {str(e)}"
            else:
                # 如果没有提供agent_handler，尝试自动获取AgentCommunication实例
                try:
                    from ...agent.communication import AgentCommunication

                    agent_comm = AgentCommunication()
                    result = await agent_comm.request_agent_assistance(agent_name, task)
                    logger.success(f"Agent {agent_name} 执行成功（自动获取Agent实例），返回: {result}")
                    return result
                except Exception as e:
                    logger.error(f"自动获取Agent实例失败: {e}")
                    return f"Agent工具调用失败: 无法获取Agent实例 - {str(e)}"

    if func_caller := get_function_calls().get(func):
        logger.info(f"Function call 请求 {func}, 参数: {arguments}")
        result = await func_caller.run(**arguments)
        logger.success(f"Function call 成功，返回: {result}")
        return result

    if mcp_result := await handle_mcp_tool(func, arguments):
        logger.success(f"MCP 工具执行成功，返回: {mcp_result}")
        return mcp_result

    return "(Unknown Function)"
