import importlib
import time
from typing import AsyncGenerator, Optional

from nonebot import logger

from .config import get_config
from .database import Database
from .llm import BasicModel
from .llm.utils.thought import process_thoughts


class Muice:
    """
    Muice交互类
    """

    def __init__(self):
        self.model_config = get_config().model
        self.think = self.model_config.think
        self.model_loader = self.model_config.loader
        self.multimodal = self.model_config.multimodal
        self.database = Database()
        self.__load_model()

    def __load_model(self) -> None:
        """
        初始化模型类
        """
        module_name = f"Muice.llm.{self.model_loader}"
        module = importlib.import_module(module_name)
        ModelClass = getattr(module, self.model_loader, None)
        self.model: Optional[BasicModel] = ModelClass(self.model_config) if ModelClass else None

    def load_model(self) -> bool:
        """
        加载模型

        return: 是否加载成功
        """
        logger.info("正在加载模型...")
        if not self.model:
            logger.error("模型加载失败")
            return False
        if not self.model.load():
            logger.error("模型加载失败")
            return False
        logger.info("模型加载成功")
        return True

    def change_model_config(self, config_name: str) -> str:
        """
        更换模型配置文件并重新加载模型
        """
        try:
            self.model_config = get_config(config_name).model
        except ValueError as e:
            return str(e)
        self.think = self.model_config.think
        self.model_loader = self.model_config.loader
        self.multimodal = self.model_config.multimodal
        self.__load_model()
        self.load_model()

        return f"已成功加载 {config_name}"

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

        history = await self.get_chat_memory(userid) if enable_history else []

        start_time = time.time()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")
        if self.multimodal:
            reply = await self.model.ask_vision(message, image_paths, history)
        else:
            reply = await self.model.ask(message, history)
        if isinstance(reply, str):
            reply.strip()
        end_time = time.time()
        logger.info(f"模型调用时长: {end_time - start_time} s")

        thought, result = process_thoughts(reply, self.think)  # type: ignore
        reply = "\n\n".join([thought, result])

        await self.database.add_item(userid, message, result, image_paths)

        return reply

    async def ask_stream(
        self,
        message: str,
        userid: str,
        image_paths: list = [],
        enable_history: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        以流式方式调用模型并逐步返回输出
        """
        if not (self.model and self.model.is_running):
            logger.error("模型未加载")
            yield "(模型未加载)"
            return

        logger.info("正在调用模型...")

        history = await self.get_chat_memory(userid) if enable_history else []

        start_time = time.time()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")

        if self.multimodal:
            response = await self.model.ask_vision(message, image_paths, history)
        else:
            response = await self.model.ask(message, history)  # 改成流式

        reply = ""

        if isinstance(response, str):
            yield response.strip()
            reply = response
        else:
            async for chunk in response:
                yield (chunk if not self.think else chunk.replace("<think>", "思考过程：").replace("</think>", ""))
                reply += chunk

        end_time = time.time()
        logger.info(f"模型调用时长: {end_time - start_time} s")

        _, result = process_thoughts(reply, self.think)  # type: ignore

        await self.database.add_item(userid, message, result, image_paths)

    async def get_chat_memory(self, userid: str) -> list:
        """
        获取记忆
        """
        history = await self.database.get_history(userid)
        if not history:
            return []

        history = [[item[3], item[4]] for item in history]
        return history

    async def refresh(self, userid: str) -> str:
        """
        刷新对话
        """
        logger.info(f"用户 {userid} 请求刷新")

        last_item = await self.database.get_last_item(userid)

        if not last_item:
            logger.error("用户对话数据不存在，拒绝刷新")
            return "你都还没和我说过一句话呢，得和我至少聊上一段才能刷新哦"
        if not (self.model and self.model.is_running):
            logger.error("模型未加载")
            return "(模型未加载)"

        userid, message = set(last_item[0][3:5])
        image_paths = last_item[0][-1]
        await self.database.remove_last_item(userid)
        history = await self.get_chat_memory(userid)

        start_time = time.time()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")
        if self.multimodal and image_paths:
            reply = await self.model.ask_vision(message, image_paths, history)
        else:
            reply = await self.model.ask(message, history)
        if isinstance(reply, str):
            reply.strip()
        end_time = time.time()
        logger.info(f"模型调用时长: {end_time - start_time} s")
        logger.info(f"模型返回：{reply}")

        thought, result = process_thoughts(reply, self.think)  # type: ignore
        reply = "\n\n".join([thought, result])

        await self.database.add_item(userid, message, result, image_paths)

        return reply

    async def reset(self, userid: str) -> str:
        """
        清空历史对话（将用户对话历史记录标记为不可用）
        """
        await self.database.mark_history_as_unavailable(userid)
        return "已成功移除对话历史~"

    async def undo(self, userid: str) -> str:
        await self.database.remove_last_item(userid)
        return "已成功撤销上一段对话~"
