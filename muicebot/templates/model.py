from typing import List

from pydantic import BaseModel, ConfigDict, Field


class Userinfo(BaseModel):
    """用户信息配置"""

    name: str
    """用户名称"""
    id: str
    """用户 Nonebot ID"""
    info: str
    """用户信息"""


class PromptTemplatesConfig(BaseModel):
    """提示词模板配置"""

    ai_nickname: str = "沐雪"
    """AI 昵称"""
    master_nickname: str = "沐沐(Muika)"
    """AI 开发者昵称"""

    userinfos: List[Userinfo] = Field(default=[])
    """用户信息列表"""

    model_config = ConfigDict(extra="allow")
    """允许其他模板参数传入"""


class PromptTemplatesData(BaseModel):
    """提示词模板数据"""

    ai_nickname: str = "沐雪"
    """AI 昵称"""
    master_nickname: str = "沐沐(Muika)"
    """AI 开发者昵称"""

    private: bool = False
    """当前对话是否为私聊"""
    user_name: str = ""
    """目标用户名"""
    user_info: str = ""
    """目标用户信息"""

    model_config = ConfigDict(extra="allow")
    """允许其他模板参数传入"""

    @classmethod
    def from_config(cls, templates_config: PromptTemplatesConfig, userid: str, is_private: bool = False):
        base = templates_config.model_dump()
        data = cls(**base)

        user = next((u for u in templates_config.userinfos if u.id == userid), None)
        if user:
            data.user_name = user.name
            data.user_info = user.info

        data.private = is_private

        return data
