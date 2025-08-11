"""
Agent工具函数模块
"""

from typing import Any, Dict, List

from muicebot.agent.config import AgentConfigManager
from muicebot.agent.tools import load_agent_tools


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
            # 获取Agent可用的工具列表 - 使用通用工具加载函数
            available_tools = await load_agent_tools(agent_name, config.tools_list)

            if available_tools:
                tools_description = ", ".join(
                    [tool.get("function", {}).get("name", "unknown") for tool in available_tools]
                )
                # 使用配置中的description字段，如果没有则使用默认描述
                agent_description = (
                    config.description
                    or f"调用{agent_name} Agent处理复杂任务。该Agent具备多种工具能力，可以使用以下工具: {tools_description}。"
                    f"当用户请求涉及复杂分析、数据处理、信息检索或多步骤操作时，应该调用此Agent。"
                    f"Agent将专注于分析并提供专业结果，后续决策由主模型控制。"
                )
            else:
                # 如果没有可用工具，提供一个通用的Agent工具
                # 使用配置中的description字段，如果没有则使用默认描述
                agent_description = (
                    config.description
                    or f"调用{agent_name} Agent处理通用任务。此Agent适用于处理各种类型的请求，"
                    f"包括问答、分析、总结、创作等。Agent将专注于分析并提供专业结果，"
                    f"后续决策由主模型控制。"
                )

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
