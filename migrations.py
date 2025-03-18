import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import aiosqlite


@dataclass
class Message:
    id: int | None = None
    """每条消息的唯一ID"""
    time: str = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
    """
    字符串形式的时间数据：%Y.%m.%d %H:%M:%S
    若要获取格式化的 datetime 对象，请使用 format_time
    """
    userid: str = ""
    """Nonebot 的用户id"""
    message: str = ""
    """消息主体"""
    respond: str = ""
    """模型回复（不包含思维过程）"""
    history: int = 1
    """消息是否可用于对话历史中，以整数形式映射布尔值"""
    images: List[str] = field(default_factory=list)
    """多模态中使用的图像，默认为空列表"""

    def __post_init__(self):
        if isinstance(self.images, str):
            self.images = json.loads(self.images)
        elif self.images is None:
            self.images = []


class Database:
    def __init__(self, db_path: str) -> None:
        self.DB_PATH = db_path

    def __connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.DB_PATH)

    async def __execute(self, query: str, params=(), fetchone=False, fetchall=False) -> list | None:
        """
        异步执行SQL查询，支持可选参数。

        :param query: 要执行的SQL查询语句
        :param params: 传递给查询的参数
        :param fetchone: 是否获取单个结果
        :param fetchall: 是否获取所有结果
        """
        async with self.__connect() as conn:
            cursor = await conn.cursor()
            await cursor.execute(query, params)
            if fetchone:
                return await cursor.fetchone()  # type: ignore
            if fetchall:
                return await cursor.fetchall()  # type: ignore
            await conn.commit()

        return None

    async def __create_database(self) -> None:
        await self.__execute(
            """CREATE TABLE MSG(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TIME TEXT NOT NULL,
            USERID TEXT NOT NULL,
            MESSAGE TEXT NOT NULL,
            RESPOND TEXT NOT NULL,
            HISTORY INTEGER NOT NULL DEFAULT (1),
            IMAGES TEXT NOT NULL DEFAULT "[]");"""
        )

    async def add_item(self, message: Message):
        """
        将消息保存到数据库
        """
        params = (message.time, message.userid, message.message, message.respond, json.dumps(message.images))
        query = """INSERT INTO MSG (TIME, USERID, MESSAGE, RESPOND, IMAGES)
                   VALUES (?, ?, ?, ?, ?)"""
        await self.__execute(query, params)


async def migrate_old_data_to_new_db(old_data_dir: str, new_database_path: str):
    db = Database(new_database_path)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 遍历 memory 目录下的 JSON 文件
    for filename in os.listdir(old_data_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(old_data_dir, filename)
        user_id = filename.replace(".json", "")

        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    data = json.loads(line.strip())
                    prompt = data.get("prompt", "").strip()
                    completion = data.get("completion", "").strip()

                    # 跳过空数据
                    if not prompt or not completion:
                        continue

                    message = Message(time=current_time, userid=user_id, message=prompt, respond=completion, images=[])

                    await db.add_item(message)

                except json.JSONDecodeError:
                    print(f"⚠️ JSON 解析失败: {file_path}")

    print("✅ 迁移完成！")


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("❌ 使用方式: python migrations.py <OLD_DATA_DIR> <NEW_DATABASE_PATH>")
        sys.exit(1)

    old_data_dir = sys.argv[1]  # 从命令行参数获取旧数据目录
    new_database_path = sys.argv[2]
    asyncio.run(migrate_old_data_to_new_db(old_data_dir, new_database_path))  # 运行异步迁移任务
