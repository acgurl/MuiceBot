import json
from pathlib import Path

from .models import InstalledPluginInfo

JSON_PATH = Path("plugins/installed_plugins.json")


def load_json_record() -> dict[str, InstalledPluginInfo]:
    """
    获取本地 json 记录
    `plugin/installed_plugins.json`
    """
    if not JSON_PATH.exists():
        return {}

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json_record(data: dict) -> None:
    """
    在本地保存 json 记录
    """
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register_plugin(plugin: str, commit: str, name: str, module: str) -> None:
    """
    在本地注册一个插件记录

    :param plugin: 插件唯一索引名
    :param commit: 插件 git commit hash值
    :param name: 插件名
    :param module: 相对于 `store` 文件夹的可导入模块名
    """
    plugins = load_json_record()
    plugins[plugin] = {"commit": commit, "module": module, "name": name}
    _save_json_record(plugins)


def unregister_plugin(plugin: str) -> None:
    """
    取消记录一个插件记录（通常在卸载插件时使用）
    """
    plugins = load_json_record()
    if plugin in plugins:
        del plugins[plugin]
        _save_json_record(plugins)
