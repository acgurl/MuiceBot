from typing import Any

from pydantic import BaseModel, Field

from ..typing import FUNCTION_CALL_FUNC


class Parameter(BaseModel):
    """
    Function_call 插件参数对象
    """

    type: str
    """参数类型描述 string integer等"""
    description: str
    """参数描述"""
    default: Any = None
    """默认值"""
    properties: dict[str, Any] = {}
    """参数定义属性，例如最大值最小值等"""
    required: bool = False
    """是否必须"""

    def data(self) -> dict[str, Any]:
        """
        生成参数描述信息

        :return: 可用于 Function_call 的字典
        """
        return {
            "type": self.type,
            "description": self.description,
            **{key: value for key, value in self.properties.items() if value is not None},
        }


class ParamTypes:
    STRING = "string"
    INTEGER = "integer"
    ARRAY = "array"
    OBJECT = "object"
    BOOLEAN = "boolean"
    NUMBER = "number"


class String(Parameter):
    type: str = ParamTypes.STRING
    properties: dict[str, Any] = Field(default_factory=dict)
    enum: list[str] | None = None


class Integer(Parameter):
    type: str = ParamTypes.INTEGER
    properties: dict[str, Any] = Field(default_factory=lambda: {"minimum": 0, "maximum": 100})

    minimum: int | None = None
    maximum: int | None = None


class Array(Parameter):
    type: str = ParamTypes.ARRAY
    properties: dict[str, Any] = Field(default_factory=lambda: {"items": {"type": "string"}})
    items: str = Field("string", description="数组元素类型")


class FunctionCall(BaseModel):
    """
    Function_call 插件函数对象(未被使用)
    """

    name: str
    """函数名称"""
    description: str
    """函数描述"""
    arguments: dict[str, Parameter]
    """函数参数信息"""
    function: FUNCTION_CALL_FUNC
    """函数对象"""
    kwargs: dict[str, Any] = {}
    """扩展参数"""

    class Config:
        arbitrary_types_allowed = True

    def __hash__(self) -> int:
        return hash(self.name)

    def data(self) -> dict[str, Any]:
        """
        生成函数描述信息

        :return: 可用于 Function_call 的字典
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {k: v.data() for k, v in self.arguments.items()},
                    "required": [k for k, v in self.arguments.items() if v.default is None],
                    "additionalProperties": False,
                },
                **self.kwargs,
            },
        }
