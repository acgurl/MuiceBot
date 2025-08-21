import json
from pathlib import Path
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

CONFIG_PATH = Path("./configs/mcp.json")


class McpServer(BaseModel):
    command: str | None = Field(default=None)
    """执行指令"""
    args: list = Field(default_factory=list)
    """命令参数"""
    env: dict[str, Any] = Field(default_factory=dict)
    """环境配置"""
    headers: dict[str, Any] = Field(default_factory=dict)
    """HTTP请求头 (用于sse和streamable_http传输方式)"""
    type: Literal["stdio", "sse", "streamable_http"] = Field(default="stdio")
    """传输方式: stdio, sse, streamable_http"""
    url: str | None = Field(default=None)
    """服务器URL (用于sse和streamable_http传输方式)"""


McpConfig = Dict[str, McpServer]


def get_mcp_server_config() -> McpConfig:
    """
    从 MCP 配置文件 `config/mcp.json` 中获取 MCP Server 配置
    """
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = json.load(f) or {}

    mcp_config: McpConfig = dict()

    for name, srv_config in configs["mcpServers"].items():
        mcp_config[name] = McpServer(**srv_config)

    return mcp_config
