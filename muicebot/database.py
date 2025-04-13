import asyncio
import json
import os
from datetime import datetime
from typing import Tuple

import aiosqlite
import nonebot_plugin_localstore as store
from nonebot import logger

from ._types import Message
from .utils.migrations import MigrationManager


class Database:
    def __init__(self) -> None:
        self.DB_PATH = store.get_plugin_data_dir().joinpath("ChatHistory.db").resolve()

        asyncio.run(self.init_db())

        logger.info(f"数据库路径: {self.DB_PATH}")

    async def init_db(self) -> None:
        """初始化数据库，检查数据库是否存在，不存在则创建"""
        if not os.path.isfile(self.DB_PATH) or self.DB_PATH.stat().st_size == 0:
            logger.info("数据库不存在，正在创建...")
            await self.__create_database()

        await MigrationManager(self).migrate_if_needed()

    def __connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.DB_PATH)

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

    async def __create_database(self) -> None:
        """
        创建一个新的信息表
        """
        await self.execute(
            """CREATE TABLE MSG(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TIME TEXT NOT NULL,
            USERID TEXT NOT NULL,
            GROUPID TEXT NOT NULL DEFAULT (-1),
            MESSAGE TEXT NOT NULL,
            RESPOND TEXT NOT NULL,
            HISTORY INTEGER NOT NULL DEFAULT (1),
            IMAGES TEXT NOT NULL DEFAULT "[]",
            TOTALTOKENS INTEGER NOT NULL DEFAULT (-1));"""
        )

    def connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.DB_PATH)

    async def add_item(self, message: Message):
        """
        将消息保存到数据库
        """
        params = (
            message.time,
            message.userid,
            message.groupid,
            message.message,
            message.respond,
            json.dumps(message.images),
            message.totaltokens,
        )
        query = """INSERT INTO MSG (TIME, USERID, GROUPID, MESSAGE, RESPOND, IMAGES, TOTALTOKENS)
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        await self.execute(query, params)

    async def mark_history_as_unavailable(self, userid: str):
        """
        将用户的所有对话历史标记为不可用 (适用于 reset 命令)

        :userid: 用户id
        """
        query = "UPDATE MSG SET HISTORY = 0 WHERE USERID = ?"
        await self.execute(query, (userid,))

    async def get_user_history(self, userid: str, limit: int = 0) -> list[Message]:
        """
        获取用户的所有对话历史，返回一个列表，无结果时返回None

        :userid: 用户id
        :limit: (可选) 返回的最大长度，当该变量设为0时表示全部返回
        """
        if limit:
            query = f"SELECT * FROM MSG WHERE HISTORY = 1 AND USERID = ? ORDER BY ID DESC LIMIT {limit}"
        else:
            query = "SELECT * FROM MSG WHERE HISTORY = 1 AND USERID = ?"
        rows = await self.execute(query, (userid,), fetchall=True)

        result = [Message(**dict(row)) for row in rows] if rows else []
        result.reverse()

        return result

    async def get_group_history(self, groupid: str, limit: int = 0) -> list[Message]:
        """
        获取群组的所有对话历史，返回一个列表，无结果时返回None

        :groupid: 群组id
        :limit: (可选) 返回的最大长度，当该变量设为0时表示全部返回
        """
        if limit:
            query = f"SELECT * FROM MSG WHERE HISTORY = 1 AND GROUPID = ? ORDER BY ID DESC LIMIT {limit}"
        else:
            query = "SELECT * FROM MSG WHERE HISTORY = 1 AND GROUPID = ?"
        rows = await self.execute(query, (groupid,), fetchall=True)

        result = [Message(**dict(row)) for row in rows] if rows else []
        result.reverse()

        return result

    async def get_model_usage(self) -> Tuple[int, int]:
        """
        获取模型用量数据（今日用量，总用量）

        :return: today_usage, total_usage
        """
        today_str = datetime.now().strftime("%Y.%m.%d")

        # 查询总用量（排除 TOTALTOKENS = -1）
        total_result = await self.execute("SELECT SUM(TOTALTOKENS) FROM MSG WHERE TOTALTOKENS != -1", fetchone=True)
        total_usage = total_result[0] if total_result else 0

        # 查询今日用量（按日期前缀匹配 TIME）
        today_result = await self.execute(
            "SELECT SUM(TOTALTOKENS) FROM MSG WHERE TOTALTOKENS != -1 AND TIME LIKE ?",
            (f"{today_str}%",),
            fetchone=True,
        )
        today_usage = today_result[0] if today_result else 0

        return today_usage, total_usage

    async def remove_last_item(self, userid: str):
        """
        删除用户的最新一条对话历史

        :userid: 用户id
        """
        query = "DELETE FROM MSG WHERE ID = (SELECT ID FROM MSG WHERE USERID = ? ORDER BY ID DESC LIMIT 1)"
        await self.execute(query, (userid,))
