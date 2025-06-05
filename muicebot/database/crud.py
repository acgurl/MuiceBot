import json
from datetime import datetime
from typing import List, Optional

from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import delete, desc, func, select, update

from ..models import Message, Resource
from .orm_models import Msg


class MessageORM:
    @staticmethod
    def _convert(row: Msg) -> Message:
        """
        反序列化为 Message 实例
        """
        return Message(
            time=row.time,
            userid=row.userid,
            groupid=row.groupid,
            message=row.message,
            respond=row.respond,
            resources=[Resource(**r) for r in json.loads(row.resources or "[]")],
            usage=row.usage,
        )

    @staticmethod
    async def add_item(session: async_scoped_session, message: Message):
        """
        将消息保存到数据库
        """
        resources = json.dumps([r.to_dict() for r in message.resources], ensure_ascii=False)
        session.add(
            Msg(
                time=message.time,
                userid=message.userid,
                groupid=message.groupid,
                message=message.message,
                respond=message.respond,
                resources=resources,
                usage=message.usage,
            )
        )

    @staticmethod
    async def get_user_history(session: async_scoped_session, userid: str, limit: int = 0) -> List[Message]:
        """
        获取用户的所有对话历史

        :param userid: 用户名
        :param limit: (可选) 返回的最大长度，当该变量设为0时表示全部返回

        :return: 消息列表
        """
        stmt = select(Msg).where(Msg.userid == userid, Msg.history == 1).order_by(desc(Msg.id))
        if limit:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [MessageORM._convert(msg) for msg in rows][::-1]

    @staticmethod
    async def get_group_history(session: async_scoped_session, groupid: str, limit: int = 0) -> List[Message]:
        """
        获取群组的所有对话历史，返回一个列表，无结果时返回None

        :param groupid: 群组id
        :param limit: (可选) 返回的最大长度，当该变量设为0时表示全部返回

        :return: 消息列表
        """
        stmt = select(Msg).where(Msg.groupid == groupid, Msg.history == 0).order_by(desc(Msg.id))
        if limit:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [MessageORM._convert(msg) for msg in rows][::-1]

    @staticmethod
    async def mark_history_as_unavailable(session: async_scoped_session, userid: str, limit: Optional[int] = None):
        """
        将用户消息上下文标记为不可用 (适用于 reset 命令)

        :param userid: 用户id
        :param limit: (可选)最大操作数
        """
        if limit:
            subq = select(Msg.id).where(Msg.userid == userid, Msg.history == 1).order_by(desc(Msg.id)).limit(limit)
            sub_ids = (await session.execute(subq)).scalars().all()
            if sub_ids:
                await session.execute(update(Msg).where(Msg.id.in_(sub_ids)).values(history=0))
        else:
            await session.execute(update(Msg).where(Msg.userid == userid).values(history=0))

    @staticmethod
    async def remove_user_history(session: async_scoped_session, userid: str, limit: int = 1):
        """
        删除用户的对话历史

        :param userid: 用户id
        :param limit: (可选)最大操作数，默认为最新一条
        """
        stmt = select(Msg).where(Msg.userid == userid).order_by(desc(Msg.id)).limit(limit)
        msg = (await session.execute(stmt)).scalar_one_or_none()
        if msg:
            await session.execute(delete(Msg).where(Msg.id == msg.id))

    @staticmethod
    async def get_model_usage(session: async_scoped_session) -> tuple[int, int]:
        """
        获取模型用量数据（今日用量，总用量）

        :return: today_usage, total_usage
        """
        total = await session.execute(select(func.sum(Msg.usage)).where(Msg.usage != -1))
        today = await session.execute(
            select(func.sum(Msg.usage)).where(Msg.usage != -1, Msg.time.like(f"{datetime.now().strftime('%Y.%m.%d')}%"))
        )
        return (today.scalar() or 0), (total.scalar() or 0)

    @staticmethod
    async def get_conv_count(session: async_scoped_session) -> tuple[int, int]:
        """
        获取对话次数（今日次数，总次数）

        :return: today_count, total_count
        """
        total = await session.execute(select(func.count()).where(Msg.usage != -1))
        today = await session.execute(
            select(func.count()).where(Msg.usage != -1, Msg.time.like(f"{datetime.now().strftime('%Y.%m.%d')}%"))
        )
        return (today.scalar() or 0), (total.scalar() or 0)
