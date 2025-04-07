import importlib
import time
from typing import AsyncGenerator, Optional, Union

from nonebot import logger

from ._types import Message
from .config import ModelConfig, get_model_config, model_config_manager, plugin_config
from .database import Database
from .llm import MODEL_DEPENDENCY_MAP, BasicModel, get_missing_dependencies
from .llm.utils.auto_system_prompt import auto_system_prompt
from .llm.utils.thought import process_thoughts, stream_process_thoughts
from .plugin import get_tools


class Muice:
    """
    Muice交互类
    """

    def __init__(self):
        self.model_config = get_model_config()
        self.think = self.model_config.think
        self.model_loader = self.model_config.loader
        self.multimodal = self.model_config.multimodal
        self.database = Database()
        self.max_history_epoch = plugin_config.max_history_epoch

        self.system_prompt: str = self.model_config.system_prompt
        self.user_instructions = self.model_config.user_instructions

        self.__load_model()

        model_config_manager.register_listener(self._on_config_changed)

    def __del__(self):
        # 注销监听器
        try:
            model_config_manager.unregister_listener(self._on_config_changed)
        except Exception:
            pass

    def __load_model(self) -> None:
        """
        初始化模型类
        """
        try:
            module_name = f"muicebot.llm.{self.model_loader}"
            module = importlib.import_module(module_name)
            ModelClass = getattr(module, self.model_loader, None)
            self.model: Optional[BasicModel] = ModelClass(self.model_config) if ModelClass else None

        except ImportError as e:
            logger.critical(f"导入模型加载器 '{self.model_loader}' 失败：{e}")
            dependencies = MODEL_DEPENDENCY_MAP.get(self.model_loader, [])
            missing = get_missing_dependencies(dependencies)
            if missing:
                install_command = "pip install " + " ".join(missing)
                logger.critical(f"缺少依赖库：{', '.join(missing)}\n请运行以下命令安装缺失项：\n\n{install_command}")

        except AttributeError as e:
            logger.critical(f"导入模型加载器 '{self.model_loader}' 失败：{e}")
            logger.critical("这有可能是负责编写模型加载器的开发者未正确命名类导致，又或者是您输入了错误的模型加载器名")

    def load_model(self) -> bool:
        """
        加载模型

        return: 是否加载成功
        """
        if not self.model:
            logger.error("模型加载失败: self.model 变量不存在")
            return False
        if not self.model.load():
            logger.error("模型加载失败: self.model.load 函数失败")
            return False
        return True

    def _on_config_changed(self, new_config: ModelConfig, old_config: ModelConfig):
        """配置文件变更时的回调函数"""
        logger.info("检测到配置文件变更，自动重载模型...")
        # 更新配置
        self.model_config = new_config
        self.think = new_config.think
        self.model_loader = new_config.loader
        self.multimodal = new_config.multimodal
        self.system_prompt = new_config.system_prompt
        self.user_instructions = new_config.user_instructions

        # 重新加载模型
        self.__load_model()
        self.load_model()
        logger.success(f"模型自动重载完成: {old_config.loader} -> {new_config.loader}")

    def change_model_config(self, config_name: str) -> str:
        """
        更换模型配置文件并重新加载模型
        """
        try:
            self.model_config = get_model_config(config_name)
        except (ValueError, FileNotFoundError) as e:
            return str(e)
        self.think = self.model_config.think
        self.model_loader = self.model_config.loader
        self.multimodal = self.model_config.multimodal
        self.__load_model()
        self.load_model()

        return f"已成功加载 {config_name}" if config_name else "未指定模型配置名，已加载默认模型配置"

    def _prepare_prompt(self, message: str) -> str:
        """
        准备提示词
        """
        if self.model_config.auto_system_prompt:
            self.system_prompt = auto_system_prompt(message)

        elif self.model_config.auto_user_instructions:
            self.user_instructions = auto_system_prompt(message)

        return f"{self.user_instructions}\n\n{message}" if self.user_instructions else message

    async def ask(
        self,
        message: str,
        userid: str,
        image_paths: list = [],
        enable_history: bool = True,
    ) -> str:
        """
        调用模型

        :param message: 消息内容
        :param image_paths: 图片URL列表（仅在多模态启用时生效）
        :param user_id: 用户ID
        :param enable_history: 启用历史记录
        :return: 模型回复
        """
        if not (self.model and self.model.is_running):
            logger.error("模型未加载")
            return "(模型未加载)"

        logger.info("正在调用模型...")

        prompt = self._prepare_prompt(message)
        history = await self.database.get_history(userid, self.max_history_epoch) if enable_history else []
        tools = get_tools() if self.model_config.function_call else []
        system = self.system_prompt if self.system_prompt else None

        start_time = time.perf_counter()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")

        reply = await self.model.ask(prompt, history, image_paths, stream=False, system=system, tools=tools)

        reply.strip()
        end_time = time.perf_counter()
        if self.model.succeed:
            logger.success(f"模型调用成功: {reply}")
        logger.debug(f"模型调用时长: {end_time - start_time} s")

        thought, result = process_thoughts(reply, self.think)  # type: ignore
        reply = "\n\n".join([thought, result])

        if self.model.succeed:
            message_object = Message(userid=userid, message=message, respond=result, images=image_paths)
            await self.database.add_item(message_object)

        return reply

    async def ask_stream(
        self, message: str, userid: str, image_paths: list = [], enable_history: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        以流式方式调用模型并逐步返回输出
        """
        if not (self.model and self.model.is_running):
            logger.error("模型未加载")
            yield "(模型未加载)"
            return

        logger.info("正在调用模型...")

        prompt = self._prepare_prompt(message)
        history = await self.database.get_history(userid, self.max_history_epoch)
        tools = get_tools() if self.model_config.function_call else []
        system = self.system_prompt if self.system_prompt else None

        start_time = time.perf_counter()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")

        response = await self.model.ask(prompt, history, image_paths, stream=True, system=system, tools=tools)

        reply = ""

        if isinstance(response, str):
            yield response.strip()
            reply = response
        else:
            async for chunk in response:
                yield (chunk if not self.think else stream_process_thoughts(chunk, self.think))  # type:ignore
                reply += chunk

        end_time = time.perf_counter()
        logger.success(f"已完成流式回复: {reply}")
        logger.debug(f"模型调用时长: {end_time - start_time} s")

        _, result = process_thoughts(reply, self.think)  # type: ignore

        if self.model.succeed:
            message_object = Message(userid=userid, message=message, respond=result, images=image_paths)
            await self.database.add_item(message_object)

    async def refresh(self, userid: str) -> Union[AsyncGenerator[str, None], str]:
        """
        刷新对话

        :userid: 用户唯一标识id
        """
        logger.info(f"用户 {userid} 请求刷新")

        last_item = await self.database.get_history(userid, limit=1)
        last_item = last_item[0]

        if not last_item:
            logger.warning("用户对话数据不存在，拒绝刷新")
            return "你都还没和我说过一句话呢，得和我至少聊上一段才能刷新哦"

        userid = last_item.userid
        message = last_item.message
        image_paths = last_item.images

        await self.database.remove_last_item(userid)

        if not self.model_config.stream:
            return await self.ask(message, userid, image_paths)

        return self.ask_stream(message, userid, image_paths)

    async def reset(self, userid: str) -> str:
        """
        清空历史对话（将用户对话历史记录标记为不可用）
        """
        await self.database.mark_history_as_unavailable(userid)
        return "已成功移除对话历史~"

    async def undo(self, userid: str) -> str:
        await self.database.remove_last_item(userid)
        return "已成功撤销上一段对话~"
