import json
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field

CONFIG_PATH = Path("./configs/mcp.json")


class mcpServer(BaseModel):
    command: str
    """执行指令"""
    args: list = Field(default_factory=list)
    """命令参数"""
    env: dict[str, Any] = Field(default_factory=dict)
    """环境配置"""


mcpConfig = Dict[str, mcpServer]


def get_mcp_server_config() -> mcpConfig:
    """
    从 MCP 配置文件 `config/mcp.json` 中获取 MCP Server 配置
    """
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = json.load(f) or {}

    mcp_config: mcpConfig = dict()

    for name, srv_config in configs["mcpServers"].items():
        mcp_config[name] = mcpServer(**srv_config)

    return mcp_config


server_config = get_mcp_server_config()
