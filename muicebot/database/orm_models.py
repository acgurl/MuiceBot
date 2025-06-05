from nonebot_plugin_orm import Model
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Msg(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time: Mapped[str] = mapped_column(String, nullable=False)
    userid: Mapped[str] = mapped_column(String, nullable=False)
    groupid: Mapped[str] = mapped_column(String, default="-1")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    respond: Mapped[str] = mapped_column(Text, nullable=False)
    history: Mapped[int] = mapped_column(Integer, default=1)
    resources: Mapped[str] = mapped_column(Text, default="[]")
    usage: Mapped[int] = mapped_column(Integer, default=-1)
