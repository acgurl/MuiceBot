import json
from pathlib import Path
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, root_validator

CONFIG_PATH = Path("./configs/mcp.json")


class McpServer(BaseModel):
    command: str | None = Field(default=None)
    """执行指令"""
    args: list[str] = Field(default_factory=list)
    """命令参数"""
    env: dict[str, Any] = Field(default_factory=dict)
    """环境配置"""
    headers: dict[str, Any] = Field(default_factory=dict)
    """HTTP请求头 (用于sse和streamable_http传输方式)"""
    type: Literal["stdio", "sse", "streamable_http"] = Field(default="stdio")
    """传输方式: stdio, sse, streamable_http"""
    url: str | None = Field(default=None)
    """服务器URL (用于sse和streamable_http传输方式)"""

    @root_validator(pre=True)
    def validate_config(cls, values):
        srv_type = values.get("type")
        command = values.get("command")
        url = values.get("url")

        if srv_type == "stdio" and not command:
            raise ValueError("当 type 为 'stdio' 时，command 字段必须存在")
        elif srv_type in ["sse", "streamable_http"] and not url:
            raise ValueError(f"当 type 为 '{srv_type}' 时，url 字段必须存在")

        return values


McpConfig = Dict[str, McpServer]


def get_mcp_server_config() -> McpConfig:
    """
    从 MCP 配置文件 `config/mcp.json` 中获取 MCP Server 配置
    """
    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            configs = json.load(f) or {}
    except json.JSONDecodeError:
        # 如果 JSON 解码失败，返回空配置
        return {}
    except Exception:
        # 处理其他可能的文件读取异常
        return {}

    mcp_config: McpConfig = dict()

    for name, srv_config in (configs.get("mcpServers") or {}).items():
        mcp_config[name] = McpServer(**srv_config)

    return mcp_config
