import json
import shutil
from pathlib import Path
from typing import Any, Literal

from nonebot import logger
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing_extensions import Self

CONFIG_PATH = Path("./configs/mcp.json")


class McpConfig(BaseModel):
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

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        srv_type = self.type
        command = self.command
        url = self.url

        if srv_type == "stdio":
            if not command:
                raise ValueError("当 type 为 'stdio' 时，command 字段必须存在")
            # 检查 command 是否为可执行的命令
            if not shutil.which(command):
                raise ValueError(f"命令 '{command}' 不存在或不可执行。")
        elif srv_type in ["sse", "streamable_http"] and not url:
            raise ValueError(f"当 type 为 '{srv_type}' 时，url 字段必须存在")

        return self


def get_mcp_server_config() -> dict[str, McpConfig]:
    """
    从 MCP 配置文件 `config/mcp.json` 中获取 MCP Server 配置
    """
    if not CONFIG_PATH.exists():
        return {}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            configs = json.load(f) or {}
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.error(f"读取MCP配置文件时发生错误: {e}")
        return {}

    if not isinstance(configs, dict):
        logger.warning("MCP配置文件顶层必须是一个JSON对象，而不是列表或其他类型。")
        return {}

    mcp_servers = configs.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        return {}

    mcp_config: dict[str, McpConfig] = {}
    for name, srv_config in mcp_servers.items():
        try:
            mcp_config[name] = McpConfig(**srv_config)
        except (ValidationError, TypeError) as e:
            logger.warning(f"无效的MCP服务器配置 '{name}': {e}")
            continue

    return mcp_config
