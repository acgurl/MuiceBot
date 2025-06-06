from pathlib import Path

import pytest
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from ..utils import ob11_private_message_event
from .utils import init_mocked_api, load_json_record


@pytest.mark.asyncio
async def test_plugin_store_show(app: App):
    async with app.test_matcher() as ctx:
        bot = ctx.create_bot()
        event = ob11_private_message_event(".store show")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "本地还未安装商店插件~", at_sender=False)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_plugin_store_install(app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path):
    mock_plugins_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.store.PLUGIN_DIR",
        new=tmp_path / "plugins" / "store",
    )
    mock_json_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.register.JSON_PATH",
        new=tmp_path / "plugins" / "installed_plugins.json",
    )
    init_mocked_api(mocked_api)

    async with app.test_matcher() as ctx:
        bot = ctx.create_bot()
        event = ob11_private_message_event(".store install searxng")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "✅ 插件 searxng 安装成功！", at_sender=False)
        ctx.should_finished()

    installed_plugin = load_json_record(mock_json_path)
    assert installed_plugin.get("searxng", None)
    assert mocked_api["plugins_list"].called
    assert (mock_plugins_path / "searxng" / "Readme.md").stat().st_size != 0


@pytest.mark.asyncio
async def test_plugin_store_update(app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path):
    mock_plugins_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.store.PLUGIN_DIR",
        new=tmp_path / "plugins" / "store",
    )
    mock_json_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.register.JSON_PATH",
        new=tmp_path / "plugins" / "installed_plugins.json",
    )
    init_mocked_api(mocked_api)

    async with app.test_matcher() as ctx:
        bot = ctx.create_bot()
        event = ob11_private_message_event(".store update searxng")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "✅ 插件 searxng 更新成功！重启后生效", at_sender=False)
        ctx.should_finished()

    installed_plugin = load_json_record(mock_json_path)
    assert installed_plugin.get("searxng", None)
    assert mocked_api["plugins_list"].called
    assert (mock_plugins_path / "searxng" / "Readme.md").stat().st_size != 0


@pytest.mark.asyncio
async def test_plugin_store_uninstall(app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path):
    mock_plugins_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.store.PLUGIN_DIR",
        new=tmp_path / "plugins" / "store",
    )
    mock_json_path = mocker.patch(
        "muicebot.builtin_plugins.muicebot_plugin_store.register.JSON_PATH",
        new=tmp_path / "plugins" / "installed_plugins.json",
    )
    init_mocked_api(mocked_api)

    async with app.test_matcher() as ctx:
        bot = ctx.create_bot()
        event = ob11_private_message_event(".store uninstall searxng")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "✅ 插件 Searxng 移除成功！重启后生效", at_sender=False)
        ctx.should_finished()

    installed_plugin = load_json_record(mock_json_path)
    assert installed_plugin.get("searxng", None) is None
    assert (mock_plugins_path / "searxng").exists() is False
