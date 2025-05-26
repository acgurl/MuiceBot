from dataclasses import dataclass, field
from typing import List, Optional

from ..models import Message, Resource


@dataclass
class ModelRequest:
    """
    模型调用请求
    """

    prompt: str
    history: List[Message] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    tools: Optional[List[dict]] = field(default_factory=list)
    system: Optional[str] = None


@dataclass
class ModelCompletions:
    """
    模型输出
    """

    text: str = ""
    usage: int = -1
    resources: List[Resource] = field(default_factory=list)
    succeed: Optional[bool] = True


@dataclass
class ModelStreamCompletions:
    """
    模型流式输出
    """

    chunk: str = ""
    usage: int = -1
    resources: Optional[List[Resource]] = field(default_factory=list)
    succeed: Optional[bool] = True
