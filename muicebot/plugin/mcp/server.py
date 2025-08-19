import asyncio
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from .config import mcpServer


class Tool:
    """
    MCP Tool
    """

    def __init__(self, name: str, description: str, input_schema: dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """
        为 llm 生成工具描述

        :return: 工具描述
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"Tool: {self.name}\n" f"Description: {self.description}\n" f"Arguments:{chr(10).join(args_desc)}" ""


class Server:
    """
    管理 MCP 服务器连接和工具执行的 Server 实例
    """

    def __init__(self, name: str, config: mcpServer) -> None:
        self.name: str = name
        self.config: mcpServer = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """
        初始化实例
        """
        # 兼容旧配置，优先使用 type 字段作为传输方式
        transport = self.config.type.lower()
        
        try:
            if transport == "stdio":
                if self.config.command is None:
                    raise ValueError("command 字段对于 stdio 传输方式是必需的")
                command = shutil.which("npx") if self.config.command == "npx" else self.config.command
                if command is None:
                    raise ValueError(f"command 字段必须为一个有效值, 且目标指令必须存在于环境变量中: {self.config.command}")

                server_params = StdioServerParameters(
                    command=command,
                    args=self.config.args,
                    env={**os.environ, **self.config.env} if self.config.env else None,
                )
                transport_context = await self.exit_stack.enter_async_context(stdio_client(server_params))
            elif transport == "sse":
                if not self.config.url:
                    raise ValueError("SSE transport requires a URL")
                transport_context = await self.exit_stack.enter_async_context(
                    sse_client(self.config.url, headers=self.config.headers)
                )
            elif transport == "streamable_http":
                if not self.config.url:
                    raise ValueError("Streamable HTTP transport requires a URL")
                transport_context = await self.exit_stack.enter_async_context(
                    streamablehttp_client(self.config.url, headers=self.config.headers)
                )
            else:
                raise ValueError(f"Unsupported transport type: {transport}")
            
            # 安全地处理不同传输客户端的返回值
            # 大多数客户端返回 (read, write) 或 (read, write, additional)
            if not transport_context or len(transport_context) < 2:
                raise ValueError(f"Unexpected transport context format for {transport} transport: expected at least 2 values, got {len(transport_context) if transport_context else 0}")
            
            read, write = transport_context[0], transport_context[1]
            
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.session = session
        except Exception as e:
            logging.error(f"初始化 MCP Server 实例时遇到错误 {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> list[Tool]:
        """
        从 MCP 服务器获得可用工具列表

        :return: 工具列表

        :raises RuntimeError: 如果服务器未启动
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools: list[Tool] = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(Tool(tool.name, tool.description, tool.inputSchema) for tool in item[1])

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Optional[dict[str, Any]] = None,
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """
        执行一个 MCP 工具

        :param tool_name: 工具名称
        :param arguments: 工具参数
        :param retries: 重试次数
        :param delay: 重试间隔

        :return: 工具执行结果

        :raises RuntimeError: 如果服务器未初始化
        :raises Exception: 工具在所有重试中均失败
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:
                attempt += 1
                logging.warning(f"Error executing tool: {e}. Attempt {attempt} of {retries}.")
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")
