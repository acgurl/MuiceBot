import json

import aiosqlite
from arclet.alconna import Alconna
from nonebot import logger
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import CommandMeta, on_alconna
from nonebot_plugin_localstore import get_plugin_data_dir
from nonebot_plugin_orm import async_scoped_session

from muicebot.database import MessageORM
from muicebot.models import Message, Resource
from muicebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="muicebot_plugin_migrations", description="从旧数据库实现中迁移", usage=".migrate"
)

COMMAND_PREFIXES = [".", "/"]

command_migrate = on_alconna(
    Alconna(COMMAND_PREFIXES, "migrate", meta=CommandMeta("从旧数据库实现中迁移")),
    priority=10,
    block=True,
    permission=SUPERUSER,
)


class Database:
    def __init__(self) -> None:
        self.DB_PATH = get_plugin_data_dir().joinpath("ChatHistory.db").resolve()

    def __connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.DB_PATH)

    async def get_version(self) -> int:
        """
        获取数据库版本号，默认值为0
        """
        result = await self.execute("SELECT version FROM schema_version", fetchone=True)
        return result[0] if result else 0

    async def execute(self, query: str, params=(), fetchone=False, fetchall=False) -> list | None:
        """
        异步执行SQL查询，支持可选参数。

        :param query: 要执行的SQL查询语句
        :param params: 传递给查询的参数
        :param fetchone: 是否获取单个结果
        :param fetchall: 是否获取所有结果
        """
        async with self.__connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.cursor()
            await cursor.execute(query, params)
            if fetchone:
                return await cursor.fetchone()  # type: ignore
            if fetchall:
                rows = await cursor.fetchall()
                return [{k.lower(): v for k, v in zip(row.keys(), row)} for row in rows]
            await conn.commit()

        return None

    def connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.DB_PATH)

    async def _deserialize_rows(self, rows: list) -> list[Message]:
        """
        反序列化数据库返回结果
        """
        result = []

        for row in rows:
            data = dict(row)

            # 反序列化 resources
            resources = json.loads(data.get("resources", "[]"))
            data["resources"] = [Resource(**r) for r in resources] if resources else []

            result.append(Message(**data))

        result.reverse()
        return result

    async def get_all_record(self) -> list[Message]:
        query = "SELECT * FROM MSG"
        rows = await self.execute(query, fetchall=True)

        result = await self._deserialize_rows(rows) if rows else []

        return result


@command_migrate.handle()
async def handle_migrate(session: async_scoped_session):
    logger.info("准备从旧数据库实现中迁移...")

    old_db_path = get_plugin_data_dir().joinpath("ChatHistory.db").resolve()

    if not old_db_path.exists():
        msg = "旧数据库文件不存在，停止迁移"
        logger.error(msg)
        await command_migrate.finish(msg)

    old_db = Database()
    old_db_version = await old_db.get_version()

    if old_db_version < 2:
        msg = "旧数据库版本低于 v2，无法迁移"
        logger.error(msg)
        await command_migrate.finish(msg)

    msg_records = await old_db.get_all_record()

    message_orm = MessageORM()

    for record in msg_records:
        await message_orm.add_item(session, record)

    await session.commit()
    msg = f"已成功迁移 {len(msg_records)} 条记录✨"
    logger.success(msg)
    await command_migrate.finish(msg)
