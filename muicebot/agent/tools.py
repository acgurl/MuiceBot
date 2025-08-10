import asyncio
from threading import Lock
from typing import Any, Dict, List, Optional

from ..llm.utils.tools import function_call_handler
from ..plugin.func_call import get_function_list
from ..plugin.mcp import get_mcp_list


class AgentToolLoader:
    """Agent通用工具加载器"""

    def __init__(self):
        self._tool_cache: Dict[str, List[dict]] = {}  # 按agent名称缓存的工具列表
        self._cache_lock = Lock()  # 缓存锁
        self._last_load_time: Dict[str, float] = {}  # 每个agent的最后加载时间

    async def load_agent_tools(self, agent_name: str, tools_list: Optional[List[str]] = None) -> List[dict]:
        """
        为指定Agent加载工具

        Args:
            agent_name: Agent名称
            tools_list: 工具列表，默认为空列表，如果为None则从配置中获取

        Returns:
            工具列表
        """
        from nonebot import logger

        from ..agent.config import AgentConfigManager

        # 如果没有提供工具列表，从配置中获取
        if tools_list is None:
            config_manager = AgentConfigManager()
            tools_list = config_manager.get_available_tools(agent_name)

        # 检查缓存是否有效
        if self._is_cache_valid(agent_name, tools_list):
            logger.debug(f"使用缓存的工具列表: agent={agent_name}")
            return self._tool_cache[agent_name]

        # 加载工具
        logger.info(f"为Agent加载工具: agent={agent_name}, tools_count={len(tools_list or [])}")
        tools = await self._load_tools_from_sources(tools_list or [])

        # 更新缓存
        with self._cache_lock:
            self._tool_cache[agent_name] = tools
            self._last_load_time[agent_name] = asyncio.get_event_loop().time()

        logger.debug(f"工具加载完成: agent={agent_name}, loaded_tools={len(tools)}")
        return tools

    def _is_cache_valid(self, agent_name: str, tools_list: List[str]) -> bool:
        """
        检查缓存是否有效

        Args:
            agent_name: Agent名称
            tools_list: 当前工具列表

        Returns:
            缓存是否有效
        """
        # 如果缓存不存在，直接返回False
        if agent_name not in self._tool_cache:
            return False

        # 缓存存在，认为有效
        # 工具列表的变化会在load_agent_tools函数中处理，会先清除缓存再重新加载
        return True

    async def _load_tools_from_sources(self, tools_list: List[str]) -> List[dict]:
        """
        从各种来源加载工具 - 使用muicebot的工具调用机制

        Args:
            tools_list: 工具名称列表

        Returns:
            工具列表
        """
        available_tools = []

        # 获取所有可用的Function Call工具
        try:
            function_tools = await get_function_list()
            for tool in function_tools:
                tool_name = tool.get("function", {}).get("name")
                if tool_name in tools_list:
                    available_tools.append(tool)
        except Exception as e:
            from nonebot import logger

            logger.warning(f"Function Call工具加载失败: error={e}")

        # 获取所有可用的MCP工具
        try:
            mcp_tools = await get_mcp_list()
            for tool in mcp_tools:
                # 检查工具名称是否在配置的工具列表中
                tool_name = tool.get("function", {}).get("name")
                if tool_name in tools_list:
                    available_tools.append(tool)
        except Exception as e:
            from nonebot import logger

            logger.warning(f"MCP工具加载失败，仅使用Function Call工具: error={e}")

        return available_tools

    def clear_agent_cache(self, agent_name: Optional[str] = None):
        """
        清除Agent的工具缓存

        Args:
            agent_name: Agent名称，如果为None则清除所有缓存
        """
        with self._cache_lock:
            if agent_name is None:
                self._tool_cache.clear()
                self._last_load_time.clear()
            else:
                self._tool_cache.pop(agent_name, None)
                self._last_load_time.pop(agent_name, None)

    def get_cached_tools(self, agent_name: str) -> Optional[List[dict]]:
        """
        获取缓存的工具列表

        Args:
            agent_name: Agent名称

        Returns:
            缓存的工具列表，如果不存在则返回None
        """
        return self._tool_cache.get(agent_name)

    async def refresh_agent_tools(self, agent_name: str) -> List[dict]:
        """
        刷新Agent的工具缓存

        Args:
            agent_name: Agent名称

        Returns:
            更新后的工具列表
        """
        self.clear_agent_cache(agent_name)
        return await self.load_agent_tools(agent_name)


# 全局工具加载器实例
_tool_loader = AgentToolLoader()


async def load_agent_tools(agent_name: str, tools_list: Optional[List[str]] = None) -> List[dict]:
    """
    为Agent加载工具的通用函数

    Args:
        agent_name: Agent名称
        tools_list: 工具列表，默认为空列表，如果为None则从配置中获取

    Returns:
        工具列表
    """
    return await _tool_loader.load_agent_tools(agent_name, tools_list)


async def agent_function_call_handler(func: str, arguments: Optional[dict] = None) -> Any:
    """
    处理Agent的工具调用 - 使用muicebot的通用工具调用机制

    Args:
        func: 工具名称
        arguments: 工具参数

    Returns:
        工具调用结果
    """
    # 获取Muice实例并传入agent_handler
    try:
        from ..muice import Muice

        muice_instance = Muice.get_instance()
        return await function_call_handler(func, arguments, muice_instance._handle_agent_tool_call)
    except Exception as e:
        from nonebot import logger

        logger.warning(f"获取Muice实例失败，使用无agent_handler的方式调用: {e}")
        return await function_call_handler(func, arguments)


def clear_agent_tool_cache(agent_name: Optional[str] = None):
    """
    清除Agent工具缓存

    Args:
        agent_name: Agent名称，如果为None则清除所有缓存
    """
    _tool_loader.clear_agent_cache(agent_name)


def get_cached_agent_tools(agent_name: str) -> List[dict]:
    """
    获取缓存的Agent工具列表

    Args:
        agent_name: Agent名称

    Returns:
        缓存的工具列表，如果不存在则返回空列表
    """
    cached_tools = _tool_loader.get_cached_tools(agent_name)
    return cached_tools if cached_tools is not None else []


async def refresh_agent_tools(agent_name: str) -> List[dict]:
    """
    刷新Agent工具缓存

    Args:
        agent_name: Agent名称

    Returns:
        更新后的工具列表
    """
    return await _tool_loader.refresh_agent_tools(agent_name)
