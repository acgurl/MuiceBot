import json
import os
import sqlite3
import time

import nonebot_plugin_localstore as store
from nonebot import logger


class Database:
    def __init__(self) -> None:
        self.DB_PATH = store.get_plugin_data_dir().joinpath("ChatHistory.db").resolve()
        logger.info(f"数据库路径: {self.DB_PATH}")
        if not os.path.isfile(self.DB_PATH):
            logger.info("数据库不存在，正在创建...")
            self.__create_database()

    def __connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.DB_PATH)

    def __execute(
        self, query: str, params=(), fetchone=False, fetchall=False
    ) -> list | None:
        """
        Executes a given SQL query with optional parameters.

        :param query: The SQL query to execute.
        :param params: The parameters to pass to the query.
        :param fetchone: Whether to fetch a single result.
        :param fetchall: Whether to fetch all results.
        """
        with self.__connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            conn.commit()

    def __create_database(self) -> None:
        self.__execute(
            """CREATE TABLE MSG(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TIME TEXT NOT NULL,
            USERNAME TEXT NOT NULL,
            USERID TEXT NOT NULL,
            GROUPID TEXT NOT NULL,
            MESSAGE TEXT NOT NULL,
            RESPOND TEXT NOT NULL,
            HISTORY INTEGER NOT NULL DEFAULT (1),
            IMAGES TEXT NOT NULL DEFAULT "[]");"""
        )

    def add_item(
        self,
        username: str,
        userid: str,
        message: str,
        respond: str,
        group_id: str = "-1",
        image_paths: list = [],
    ):
        current_time = time.strftime("%Y.%m.%d %H:%M:%S")
        query = """INSERT INTO MSG (TIME, USERNAME, USERID, MESSAGE, RESPOND, GROUPID, IMAGES)
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.__execute(
            query,
            (
                current_time,
                username,
                userid,
                message,
                respond,
                group_id,
                json.dumps(image_paths),
            ),
        )

    def mark_history_as_unavailable(self, userid: str):
        query = "UPDATE MSG SET HISTORY = 0 WHERE USERID = ?"
        self.__execute(query, (userid,))

    def get_history(self, userid: str) -> list | None:
        query = "SELECT * FROM MSG WHERE HISTORY = 1 AND USERID = ?"
        return self.__execute(query, (userid,), fetchall=True)

    def get_last_item(self, userid: str) -> list | None:
        query = "SELECT * FROM MSG WHERE HISTORY = 1 AND USERID = ? ORDER BY ID DESC LIMIT 1"
        return self.__execute(query, (userid,), fetchall=True)

    def remove_last_item(self, userid: str):
        query = "DELETE FROM MSG WHERE ID = (SELECT ID FROM MSG WHERE USERID = ? ORDER BY ID DESC LIMIT 1)"
        self.__execute(query, (userid,))
