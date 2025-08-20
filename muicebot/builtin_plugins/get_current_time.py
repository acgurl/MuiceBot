from typing import Optional

from nonebot import get_plugin_config
from pydantic import BaseModel, Field, field_validator

from muicebot.plugin import PluginMetadata
from muicebot.plugin.func_call import on_function_call

__plugin_meta__ = PluginMetadata(
    name="muicebot-plugin-time",
    description="时间插件",
    usage="直接调用，返回 %Y-%m-%d %H:%M:%S 格式的当前时间",
)


class Config(BaseModel):
    timezone: Optional[str] = Field(default=None,
                                    description="当前时区",
                                    examples=["Asia/Shanghai"])

    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return value

        import pytz

        try:
            pytz.timezone(value)
            return value
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"未知的时区: {value}")


config = get_plugin_config(Config)


@on_function_call(description="获取当前时间", )
async def get_current_time() -> str:
    """
    获取当前时间
    """
    import datetime

    if config.timezone:
        import pytz

        tz = pytz.timezone(config.timezone)
    else:
        tz = None

    current_time = datetime.datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
    return current_time
