from typing import List, Optional
from pydantic import BaseModel
from ..llm._config import ModelConfig

class AgentConfig(ModelConfig):
    """Agent配置模型，继承自ModelConfig"""
    tools_list: List[str] = []
    max_loop_count: int = 5

class AgentResponse(BaseModel):
    """Agent响应模型"""
    result: str
    need_continue: bool = False
    next_agent: Optional[str] = None
    next_task: Optional[str] = None

class AgentToolCall(BaseModel):
    """Agent工具调用模型"""
    name: str
    arguments: dict
    result: Optional[str] = None