"""
Agent工具函数模块
"""

from typing import Any, Dict, List

from muicebot.agent.config import AgentConfigManager


async def get_agent_list() -> List[Dict[str, Any]]:
    """
    获取所有可用Agent的信息列表，格式化为工具调用格式

    Returns:
        List[Dict[str, Any]]: Agent信息列表，格式化为工具调用格式
    """
    agent_tools = []
    config_manager = AgentConfigManager()
    agents = config_manager.list_agents()

    # 为每个Agent创建工具描述
    for agent_name in agents:
        try:
            config = config_manager.get_agent_config(agent_name)
            # Agent本身就是工具，无论是否启用工具调用都应该添加到工具列表中
            # 使用配置中的description字段，如果没有则不提供描述
            agent_description = config.description

            agent_tool = {
                "type": "function",
                "function": {
                    "name": f"agent_{agent_name}",
                    "description": agent_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": f"要交给{agent_name} Agent处理的详细任务描述。请清晰、具体地描述任务目标、要求和期望结果，"
                                f"以便Agent能够准确理解和执行。",
                            }
                        },
                        "required": ["task"],
                    },
                },
            }
            agent_tools.append(agent_tool)
        except Exception as e:
            from nonebot import logger

            logger.warning(f"获取Agent配置失败，跳过该Agent: agent_name={agent_name}, error={e}")
            continue

    return agent_tools
