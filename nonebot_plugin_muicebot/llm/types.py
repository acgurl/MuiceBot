from abc import ABCMeta, abstractmethod
from nonebot import logger

class BasicModel(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.is_running = False

    @abstractmethod
    def load(self, model_config) -> bool:
        '''
        加载模型

        :param model_config: 模型配置
        :return: 是否加载成功
        '''
        pass

    @abstractmethod
    def ask(self, prompt:str, history:list) -> str:
        """
        模型交互询问
        
        :param prompt: 询问的内容
        :param history: 询问历史记录
        :return: 模型回复
        """
        pass

    def ask_vision(self, prompt, image_paths: list, history=None) -> str:
        """
        多模态：图像识别

        :param image_paths: 图片路径列表
        :return: 图片描述
        """
        logger.error(f'模型加载器 {self.__qualname__} 不是多模态的')
        return f'模型加载器 {self.__qualname__} 不是多模态的'