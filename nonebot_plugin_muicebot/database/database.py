from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column


class ChatHistory(Model):
    '''
    基本对话数据库模型
    '''
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    user_name: Mapped[str] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    response: Mapped[str] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    history: Mapped[bool] = mapped_column(nullable=False, default=True)