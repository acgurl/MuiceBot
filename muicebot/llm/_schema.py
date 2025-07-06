from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Literal, Optional, Type

from pydantic import BaseModel

from ..models import Message, Resource

if TYPE_CHECKING:
    from numpy import ndarray


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
    format: Literal["string", "json"] = "string"
    json_schema: Optional[Type[BaseModel]] = None


@dataclass
class ModelCompletions:
    """
    模型输出
    """

    text: str = ""
    usage: int = -1
    resources: List[Resource] = field(default_factory=list)
    succeed: bool = True


@dataclass
class ModelStreamCompletions:
    """
    模型流式输出
    """

    chunk: str = ""
    usage: int = -1
    resources: Optional[List[Resource]] = field(default_factory=list)
    succeed: bool = True


@dataclass
class EmbeddingsBatchResult:
    """
    嵌入输出
    """

    embeddings: List[List[float]]
    usage: int = -1
    succeed: bool = True

    @property
    def array(self) -> List["ndarray"]:
        from numpy import array

        return [array(embedding) for embedding in self.embeddings]
