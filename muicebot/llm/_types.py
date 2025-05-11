from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from importlib.util import find_spec
from typing import Any, AsyncGenerator, List, Literal, Optional, Union, overload

from pydantic import BaseModel, field_validator

from ..models import Message, Resource
from ..plugin import get_function_calls


class ModelConfig(BaseModel):
    loader: str = ""
    """所使用加载器的名称，位于 llm 文件夹下，loader 开头必须大写"""

    template: Optional[str] = None
    """使用的人设模板名称"""
    template_mode: Literal["system", "user"] = "system"
    """模板嵌入模式: `system` 为嵌入到系统提示; `user` 为嵌入到用户提示中"""

    max_tokens: int = 4096
    """最大回复 Tokens """
    temperature: float = 0.75
    """模型的温度系数"""
    top_p: float = 0.95
    """模型的 top_p 系数"""
    top_k: float = 3
    """模型的 top_k 系数"""
    frequency_penalty: Optional[float] = None
    """模型的频率惩罚"""
    presence_penalty: Optional[float] = None
    """模型的存在惩罚"""
    repetition_penalty: Optional[float] = None
    """模型的重复惩罚"""
    stream: bool = False
    """是否使用流式输出"""
    online_search: bool = False
    """是否启用联网搜索（原生实现）"""
    function_call: bool = False
    """是否启用工具调用"""
    content_security: bool = False
    """是否启用内容安全"""

    model_path: str = ""
    """本地模型路径"""
    adapter_path: str = ""
    """基于 model_path 的微调模型或适配器路径"""

    model_name: str = ""
    """所要使用模型的名称"""
    api_key: str = ""
    """在线服务的 API KEY"""
    api_secret: str = ""
    """在线服务的 api secret """
    api_host: str = ""
    """自定义 API 地址"""

    extra_body: Optional[dict] = None
    """OpenAI 的 extra_body"""
    enable_thinking: Optional[bool] = None
    """Dashscope 的 enable_thinking"""
    thinking_budget: Optional[int] = None
    """Dashscope 的 thinking_budget"""

    multimodal: bool = False
    """是否为（或启用）多模态模型"""
    modalities: List[Literal["text", "audio", "image"]] = ["text"]
    """生成模态"""
    audio: Optional[Any] = None
    """多模态音频参数"""

    @field_validator("loader")
    @classmethod
    def check_model_loader(cls, loader) -> str:
        if not loader:
            raise ValueError("loader is required")

        # Check if the specified loader exists
        module_path = f"muicebot.llm.{loader}"

        # 使用 find_spec 仅检测模块是否存在，不实际导入
        if find_spec(module_path) is None:
            raise ValueError(f"指定的模型加载器 '{loader}' 不存在于 llm 目录中")

        return loader


class BasicModel(metaclass=ABCMeta):
    """
    模型基类，所有模型加载器都必须继承于该类

    推荐使用该基类中定义的方法构建模型加载器类，但无论如何都必须实现 `ask` 方法
    """

    def __init__(self, model_config: ModelConfig) -> None:
        """
        统一在此处声明变量
        """
        self.config = model_config
        """模型配置"""
        self.is_running = False
        """模型状态"""
        self._total_tokens = -1
        """本次总请求（包括工具调用）使用的总token数。当此值设为-1时，表明此模型加载器不支持该功能"""

    def _require(self, *require_fields: str):
        """
        通用校验方法：检查指定的配置项是否存在，不存在则抛出错误

        :param require_fields: 需要检查的字段名称（字符串）
        """
        missing_fields = [field for field in require_fields if not getattr(self.config, field, None)]
        if missing_fields:
            raise ValueError(f"对于 {self.config.loader} 以下配置是必需的: {', '.join(missing_fields)}")

    def _build_messages(self, request: "ModelRequest") -> list:
        """
        构建对话上下文历史的函数
        """
        raise NotImplementedError

    def load(self) -> bool:
        """
        加载模型（通常是耗时操作，在线模型如无需校验可直接返回 true）

        :return: 是否加载成功
        """
        self.is_running = True
        return True

    async def _ask_sync(self, messages: list) -> "ModelCompletions":
        """
        同步模型调用
        """
        raise NotImplementedError

    def _ask_stream(self, messages: list) -> AsyncGenerator["ModelStreamCompletions", None]:
        """
        流式输出
        """
        raise NotImplementedError

    @overload
    async def ask(self, request: "ModelRequest", *, stream: Literal[False] = False) -> "ModelCompletions": ...

    @overload
    async def ask(
        self, request: "ModelRequest", *, stream: Literal[True] = True
    ) -> AsyncGenerator["ModelStreamCompletions", None]: ...

    @abstractmethod
    async def ask(
        self, request: "ModelRequest", *, stream: bool = False
    ) -> Union["ModelCompletions", AsyncGenerator["ModelStreamCompletions", None]]:
        """
        模型交互询问

        :param request: 模型调用请求体
        :param stream: 是否开启流式对话

        :return: 模型输出体
        """
        pass


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


class FunctionCallRequest(BaseModel):
    """
    模型 FunctionCall 请求
    """

    func: str
    """函数名称"""
    arguments: dict[str, str] | None = None
    """函数参数"""


async def function_call_handler(func: str, arguments: dict[str, str] | None = None) -> Any:
    """
    模型 Function Call 请求处理
    """
    arguments = arguments if arguments and arguments != {"dummy_param": ""} else {}
    func_caller = get_function_calls().get(func)
    return await func_caller.run(**arguments) if func_caller else "(Unknown Function)"
