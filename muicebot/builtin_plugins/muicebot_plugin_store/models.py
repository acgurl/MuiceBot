from typing import TypedDict


class PluginInfo(TypedDict):
    module: str
    """插件模块名"""
    name: str
    """插件名称"""
    description: str
    """插件描述"""
    repo: str
    """插件 repo 地址"""
