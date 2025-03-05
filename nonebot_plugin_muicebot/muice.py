import importlib
import time
from typing import Optional

from nonebot import logger

from .config import Config, config, get
from .database import Database
from .llm import BasicModel
from .llm.utils.thought import process_thoughts


class Muice:
    """
    Muice交互类
    """

    def __init__(self, model_config=config.model):
        self.model_config = model_config
        self.think = self.model_config.get("think", 0)
        self.model_loader = self.model_config.get("loader", "")
        self.multimodal = self.model_config.get("multimodal", False)
        self.database = Database()
        self.__load_model()

    def __load_model(self) -> None:
        """
        初始化模型类
        """
        module_name = f"nonebot_plugin_muicebot.llm.{self.model_loader}"
        module = importlib.import_module(module_name)
        ModelClass = getattr(module, self.model_loader, None)
        self.model: Optional[BasicModel] = ModelClass() if ModelClass else None

    def load_model(self) -> bool:
        """
        加载模型

        return: 是否加载成功
        """
        logger.info("正在加载模型...")
        if not self.model:
            logger.error("模型加载失败")
            return False
        if not self.model.load(self.model_config):
            logger.error("模型加载失败")
            return False
        logger.info("模型加载成功")
        return True

    def change_model_config(self, config_name: str) -> str:
        """
        更换模型配置文件并重新加载模型
        """
        if not hasattr(config, config_name):
            logger.error("指定的模型配置不存在")
            return "指定的模型配置不存在"

        model_config = getattr(config, config_name)
        new_config = get()
        new_config.update({"model": model_config})
        try:
            Config(**new_config)  # 校验模型配置可用性
        except ValueError as e:
            logger.error(f"模型配置文件加载出现问题: {e}")
            return "指定的模型加载器不存在或配置有误，请检查配置文件"

        self.model_config = model_config
        self.think = self.model_config.get("think", 0)
        self.model_loader = self.model_config.get("loader", "")
        self.multimodal = self.model_config.get("multimodal", False)
        self.__load_model()
        self.load_model()

        return f"已成功加载 {config_name}"

    def ask(
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

        history = self.get_chat_memory(userid) if enable_history else []

        start_time = time.time()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")
        if self.multimodal:
            reply = self.model.ask_vision(message, image_paths, history).strip()
        else:
            reply = self.model.ask(message, history).strip()
        end_time = time.time()
        logger.info(f"模型调用时长: {end_time - start_time} s")

        thought, result = process_thoughts(reply, self.think)
        reply = "".join([thought, result])

        self.database.add_item(userid, message, result, image_paths)

        return reply

    def get_chat_memory(self, userid: str) -> list:
        """
        获取记忆
        """
        history = self.database.get_history(userid)
        if not history:
            return []

        history = [[item[3], item[4]] for item in history]
        return history

    def refresh(self, userid: str) -> str:
        """
        刷新对话
        """
        logger.info(f"用户 {userid} 请求刷新")

        last_item = self.database.get_last_item(userid)

        if not last_item:
            logger.error("用户对话数据不存在，拒绝刷新")
            return "你都还没和我说过一句话呢，得和我至少聊上一段才能刷新哦"
        if not (self.model and self.model.is_running):
            logger.error("模型未加载")
            return "(模型未加载)"

        userid, message = set(last_item[0][3:5])
        image_paths = last_item[0][-1]
        self.database.remove_last_item(userid)
        history = self.get_chat_memory(userid)

        start_time = time.time()
        logger.debug(f"模型调用参数：Prompt: {message}, History: {history}")
        if self.multimodal and image_paths:
            reply = self.model.ask_vision(message, image_paths, history).strip()
        else:
            reply = self.model.ask(message, history).strip()
        end_time = time.time()
        logger.info(f"模型调用时长: {end_time - start_time} s")
        logger.info(f"模型返回：{reply}")

        thought, result = process_thoughts(reply, self.think)
        reply = "".join([thought, result])

        self.database.add_item(userid, message, result, image_paths)

        return reply

    def reset(self, userid: str) -> str:
        """
        清空历史对话（将用户对话历史记录标记为不可用）
        """
        self.database.mark_history_as_unavailable(userid)
        return "已成功移除对话历史~"

    def undo(self, userid: str) -> str:
        self.database.remove_last_item(userid)
        return "已成功撤销上一段对话~"
