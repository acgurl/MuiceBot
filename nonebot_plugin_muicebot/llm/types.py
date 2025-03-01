from abc import ABCMeta, abstractmethod

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

    def query_image(self, image:str) -> str:
        """
        查询图片

        :param image: 图片路径
        :return: 图片描述
        """
        return ''