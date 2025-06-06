import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from nonebug import NONEBOT_INIT_KWARGS, NONEBOT_START_LIFESPAN, App
from pytest_asyncio import is_async_test
from respx import MockRouter

from .models import BotInfo


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "sqlalchemy_database_url": "sqlite+aiosqlite://",
        "SUPERUSERS": [BotInfo.superuser_id.__str__()],
    }
    config.stash[NONEBOT_START_LIFESPAN] = False


def pytest_collection_modifyitems(items: list[pytest.Item]):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(autouse=True)
async def after_nonebot_init(after_nonebot_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)

    await driver._lifespan.startup()

    nonebot.load_from_toml("pyproject.toml")


@pytest.fixture
async def app(app: App):
    from nonebot_plugin_orm import init_orm

    await init_orm()
    yield app


@pytest.fixture
def mocked_api(respx_mock: MockRouter):
    return respx_mock
