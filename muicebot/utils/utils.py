import base64
import mimetypes
import os
import ssl
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from typing import Optional

import fleep
import httpx
import nonebot_plugin_localstore as store
from nonebot import get_bot, logger
from nonebot.adapters import Event, MessageSegment
from nonebot.log import default_filter, logger_id
from nonebot_plugin_userinfo import get_user_info

from ..config import plugin_config
from ..models import Resource
from ..plugin.context import get_event
from .adapters import ADAPTER_CLASSES

IMG_DIR = store.get_plugin_data_dir() / ".cache" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

User_Agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    "AppleWebKit/537.36 (KHTML, like Gecko)"
    "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
)


async def download_file(file_url: str, file_name: Optional[str] = None, proxy: Optional[str] = None) -> str:
    """
    保存文件至本地目录

    :param file_url: 图片在线地址
    :param file_name: 要保存的文件名
    :param proxy: 代理地址

    :return: 保存后的本地目录
    """
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT")
    file_name = file_name if file_name else str(time.time_ns()) + ".jpg"

    async with httpx.AsyncClient(proxy=proxy, verify=ssl_context) as client:
        r = await client.get(file_url, headers={"User-Agent": User_Agent})
        local_path = (IMG_DIR / file_name).resolve()
        with open(local_path, "wb") as file:
            file.write(r.content)
        return str(local_path)


async def save_image_as_base64(image_url: str, proxy: Optional[str] = None) -> str:
    """
    从在线 url 获取图像 Base64

    :image_url: 图片在线地址
    :return: 本地地址
    """
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT")

    async with httpx.AsyncClient(proxy=proxy, verify=ssl_context) as client:
        r = await client.get(image_url, headers={"User-Agent": User_Agent})
        image_base64 = base64.b64encode(r.content)
    return image_base64.decode("utf-8")


async def get_file_via_adapter(message: MessageSegment, event: Event) -> Optional[str]:
    """
    通过适配器自有方式获取文件地址并保存到本地

    :return: 本地地址
    """
    bot = get_bot()

    Onebotv12Bot = ADAPTER_CLASSES["onebot_v12"]
    UnsupportedParam = ADAPTER_CLASSES["UnsupportedParam"]
    Onebotv11Bot = ADAPTER_CLASSES["onebot_v11"]
    TelegramEvent = ADAPTER_CLASSES["telegram_event"]
    TelegramFile = ADAPTER_CLASSES["telegram_file"]

    if Onebotv12Bot and UnsupportedParam and isinstance(bot, Onebotv12Bot):
        # if message.type != "image":
        #     return None

        try:
            file_path = await bot.get_file(type="url", file_id=message.data["file_id"])
        except UnsupportedParam as e:
            logger.error(f"Onebot 实现不支持获取文件 URL，文件获取操作失败：{e}")
            return None

        return str(file_path)

    elif Onebotv11Bot and isinstance(bot, Onebotv11Bot):
        if "url" in message.data and "file" in message.data:
            return await download_file(message.data["url"], message.data["file"])

    elif TelegramEvent and TelegramFile and isinstance(event, TelegramEvent):
        if not isinstance(message, TelegramFile):
            return None

        file_id = message.data["file"]
        file = await bot.get_file(file_id=file_id)
        if not file.file_path:
            return None

        url = f"https://api.telegram.org/file/bot{bot.bot_config.token}/{file.file_path}"  # type: ignore
        # filename = file.file_path.split("/")[1]
        return await download_file(url, proxy=plugin_config.telegram_proxy)

    return None


def init_logger():
    console_handler_level = plugin_config.log_level

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    log_file_path = f"{log_dir}/{time.strftime('%Y-%m-%d')}.log"

    # 移除 NoneBot 默认的日志处理器
    logger.remove(logger_id)
    # 添加新的日志处理器
    logger.add(
        sys.stdout,
        level=console_handler_level,
        diagnose=True,
        format="<lvl>[{level}] {function}: {message}</lvl>",
        filter=default_filter,
        colorize=True,
    )

    logger.add(
        log_file_path,
        level="DEBUG",
        format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {function}: {message}",
        encoding="utf-8",
        rotation="1 day",
        retention="7 days",
    )


def get_version() -> str:
    """
    获取当前版本号

    优先尝试从已安装包中获取版本号, 否则从 `pyproject.toml` 读取
    """
    package_name = "muicebot"

    try:
        return version(package_name)
    except PackageNotFoundError:
        pass

    toml_path = os.path.join(os.path.dirname(__file__), "../pyproject.toml")

    if not os.path.isfile(toml_path):
        return "Unknown"

    try:
        if sys.version_info >= (3, 11):
            import tomllib

            with open(toml_path, "rb") as f:
                pyproject_data = tomllib.load(f)

        else:
            import toml

            with open(toml_path, "r", encoding="utf-8") as f:
                pyproject_data = toml.load(f)

        # 返回版本号
        return pyproject_data["tool"]["pdm"]["version"]

    except (FileNotFoundError, KeyError, ModuleNotFoundError):
        return "Unknown"


async def get_username(user_id: Optional[str] = None) -> str:
    """
    获取当前对话的用户名，如果失败就返回用户id
    """
    bot = get_bot()
    event = get_event()
    user_id = user_id if user_id else event.get_user_id()
    user_info = await get_user_info(bot, event, user_id)
    return user_info.user_name if user_info else user_id


def guess_mimetype(resource: Resource) -> Optional[str]:
    """
    尝试获取 minetype 类型
    """
    # raw 不落库，因此无法从 raw 判断
    if resource.path and os.path.exists(resource.path):
        try:
            with open(resource.path, "rb") as file:
                header = file.read(128)
                info = fleep.get(header)
                if info.mime:
                    return info.mime[0]  # type:ignore
                else:
                    return mimetypes.guess_type(resource.path)[0]
        except Exception:
            return mimetypes.guess_type(resource.path)[0]
    elif resource.url:
        return mimetypes.guess_type(resource.url)[0]
    return None
