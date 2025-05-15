from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite
from nonebot import logger

if TYPE_CHECKING:
    from ..database import Database


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.path: Path = db.DB_PATH

        self.migrations = {0: self._migrate_v0_to_v1, 1: self._migrate_v1_to_v2}

        self.latest_version = max(self.migrations.keys()) + 1

    async def migrate_if_needed(self):
        """
        检查数据库更新并迁移
        """
        await self.__init_version_table()
        current_version = await self.__get_version()

        while current_version in self.migrations:
            logger.info(f"检测到数据库更新，当前版本 v{current_version}...")
            backup_path = self.path.with_suffix(f".backup.v{current_version}.db")
            shutil.copyfile(self.path, backup_path)

            try:
                async with self.db.connect() as conn:
                    await conn.execute("BEGIN")
                    await self.migrations[current_version](conn)
                    await conn.commit()
                current_version += 1
                await self.__set_version(current_version)
                logger.success(f"数据库已成功迁移到 v{current_version} ⭐")
            except Exception as e:
                logger.error(f"迁移至 v{current_version + 1} 失败，错误：{e}")
                shutil.copyfile(backup_path, self.path)
                logger.info("已回退到迁移前的状态")
                break

    async def __init_version_table(self):
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );
        """
        )
        result = await self.db.execute("SELECT COUNT(*) FROM schema_version", fetchone=True)
        if not result or result[0] == 0:  # 只有 v0.2.x 的数据库没有版本号
            await self.db.execute("INSERT INTO schema_version (version) VALUES (0)")
            logger.info("数据库无版本记录，可能是v0版本的数据库，设为v0")

    async def __get_version(self) -> int:
        """
        获取数据库版本号，默认值为0
        """
        result = await self.db.execute("SELECT version FROM schema_version", fetchone=True)
        return result[0] if result else 0

    async def __set_version(self, version: int):
        await self.db.execute("UPDATE schema_version SET version = ?", (version,))

    async def _migrate_v0_to_v1(self, conn: aiosqlite.Connection):
        logger.info("v1 更新内容: 添加 TOTALTOKENS 与 GROUPID 字段")
        await conn.execute("ALTER TABLE MSG ADD COLUMN TOTALTOKENS INTEGER DEFAULT -1;")
        await conn.execute("ALTER TABLE MSG ADD COLUMN GROUPID TEXT DEFAULT '-1';")

    async def _migrate_v1_to_v2(self, conn: aiosqlite.Connection):
        logger.info("v2 更新内容: total_token 变更为 usage, images 列表优化为 resources")

        # 创建临时表
        await conn.execute(
            """
        CREATE TABLE MSG_NEW(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TIME TEXT NOT NULL,
            USERID TEXT NOT NULL,
            GROUPID TEXT NOT NULL DEFAULT (-1),
            MESSAGE TEXT NOT NULL,
            RESPOND TEXT NOT NULL,
            HISTORY INTEGER NOT NULL DEFAULT (1),
            RESOURCES TEXT NOT NULL DEFAULT "[]",
            USAGE INTEGER NOT NULL DEFAULT (-1)
        );
        """
        )

        cursor = await conn.execute(
            "SELECT ID, TIME, USERID, GROUPID, MESSAGE, RESPOND, HISTORY, IMAGES, TOTALTOKENS FROM MSG"
        )
        rows = await cursor.fetchall()

        for row in rows:
            id_, time_, userid, groupid, message, respond, history, images_json, totaltokens = row

            # 转换 images -> resources
            try:
                images = json.loads(images_json) if images_json else []
            except Exception:
                images = []

            resources = []
            for url in images:
                resources.append({"type": "image", "path": url})
            resources_json = json.dumps(resources, ensure_ascii=False)

            # 插入到新表
            await conn.execute(
                """
            INSERT INTO MSG_NEW (ID, TIME, USERID, GROUPID, MESSAGE, RESPOND, HISTORY, RESOURCES, USAGE)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (id_, time_, userid, groupid, message, respond, history, resources_json, totaltokens),
            )

        await conn.execute("DROP TABLE MSG")
        await conn.execute("ALTER TABLE MSG_NEW RENAME TO MSG")
