from dataclasses import asdict, dataclass, field
from datetime import datetime
from io import BytesIO
from typing import List, Literal, Union


@dataclass
class Resource:
    """多模态消息"""

    type: Literal["image", "video", "audio", "file"]
    """消息类型"""
    url: str = ""
    """存储地址"""
    raw: Union[bytes, BytesIO] = b""
    """二进制数据（只使用于模型返回且不保存到数据库中）"""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "url": self.url,
        }


@dataclass
class Message:
    """格式化后的 bot 消息"""

    id: int | None = None
    """每条消息的唯一ID"""
    time: str = field(default_factory=lambda: datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))
    """
    字符串形式的时间数据：%Y.%m.%d %H:%M:%S
    若要获取格式化的 datetime 对象，请使用 format_time
    """
    userid: str = ""
    """Nonebot 的用户id"""
    groupid: str = "-1"
    """群组id，私聊设为-1"""
    message: str = ""
    """消息主体"""
    respond: str = ""
    """模型回复（不包含思维过程）"""
    history: int = 1
    """消息是否可用于对话历史中，以整数形式映射布尔值"""
    resources: List[Resource] = field(default_factory=list)
    """多模态消息内容"""
    usage: int = -1
    """使用的总 tokens, 若模型加载器不支持则设为-1"""

    @property
    def format_time(self) -> datetime:
        """将时间字符串转换为 datetime 对象"""
        return datetime.strptime(self.time, "%Y.%m.%d %H:%M:%S")

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Message":
        return Message(**data)

    # 又臭又长的比较函数
    def __hash__(self) -> int:
        return hash(self.id)

    def __lt__(self, other: "Message") -> bool:
        return self.format_time < other.format_time

    def __le__(self, other: "Message") -> bool:
        return self.format_time <= other.format_time

    def __gt__(self, other: "Message") -> bool:
        return self.format_time > other.format_time

    def __ge__(self, other: "Message") -> bool:
        return self.format_time >= other.format_time
