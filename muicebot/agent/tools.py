from nonebot import logger

from muicebot.agent.config import AgentConfigManager
from muicebot.plugin.func_call import get_function_list
from muicebot.plugin.mcp import get_mcp_list


class AgentToolLoader:
    """Agent通用工具加载器"""

    def __init__(self) -> None:
        pass

    async def load_agent_tools(self, agent_name: str, tools_list: list[str] | None = None) -> list[dict]:
        """
        为指定Agent加载工具

        Args:
            agent_name: Agent名称
            tools_list: 工具列表，默认为空列表，如果为None则从配置中获取

        Returns:
            工具列表
        """
        # 如果没有提供工具列表，从配置中获取
        if tools_list is None:
            config_manager = AgentConfigManager.get_instance()
            tools_list = config_manager.get_available_tools(agent_name)

        # 加载工具
        logger.info(f"为Agent加载工具: agent={agent_name}, tools_count={len(tools_list or [])}")
        tools = await self._load_tools_from_sources(tools_list or [])

        logger.debug(f"工具加载完成: agent={agent_name}, loaded_tools={len(tools)}")
        return tools

    async def _load_tools_from_sources(self, tools_list: list[str]) -> list[dict]:
        """
        从各种来源加载工具 - 使用muicebot的工具调用机制

        Args:
            tools_list: 工具名称列表

        Returns:
            工具列表
        """
        available_tools = []

        def _filter_tools(source_tools: list[dict], source_name: str) -> None:
            """过滤工具列表"""
            for tool in source_tools:
                tool_name = tool.get("function", {}).get("name")
                if tool_name in tools_list:
                    available_tools.append(tool)

        # 获取所有可用的Function Call工具
        try:
            function_tools = await get_function_list()
            _filter_tools(function_tools, "Function Call")
        except Exception as e:
            logger.warning(f"Function Call工具加载失败: error={e}")

        # 获取所有可用的MCP工具
        try:
            mcp_tools = await get_mcp_list()
            _filter_tools(mcp_tools, "MCP")
        except Exception as e:
            logger.warning(f"MCP工具加载失败，仅使用Function Call工具: error={e}")
        return available_tools


# 全局工具加载器实例

_tool_loader = AgentToolLoader()


async def load_agent_tools(agent_name: str, tools_list: list[str] | None = None) -> list[dict]:
    """
    为Agent加载工具的通用函数

    Args:
        agent_name: Agent名称
        tools_list: 工具列表，默认为空列表，如果为None则从配置中获取

    Returns:
        工具列表
    """
    return await _tool_loader.load_agent_tools(agent_name, tools_list)
