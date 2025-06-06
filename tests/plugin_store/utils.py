import json
from pathlib import Path
from typing import TypedDict

from respx import MockRouter


class InstalledPluginInfo(TypedDict):
    module: str
    """插件模块名"""
    name: str
    """插件名称"""
    commit: str
    """commit 信息"""


def get_response_json(path: Path) -> dict:
    return json.loads(path.read_text())


def init_mocked_api(mocked_api: MockRouter) -> None:
    mocked_api.get(
        "https://raw.githubusercontent.com/MuikaAI/Muicebot-Plugins-Index/refs/heads/main/plugins.json",
        name="plugins_list",
    ).respond(json=get_response_json(Path(__file__).parent / "plugins.json"))


def load_json_record(json_path: Path) -> dict[str, InstalledPluginInfo]:
    if not json_path.exists():
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
