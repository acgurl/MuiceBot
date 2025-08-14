import time
from typing import ClassVar, Dict, Optional

from nonebot import logger

from muicebot.agent.chain import TaskChain
from muicebot.agent.config import AgentResponse
from muicebot.agent.manager import AgentManager


class AgentCommunication:
    """Agent与主模型通信接口"""

    _instance: ClassVar[Optional["AgentCommunication"]] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self.agent_manager = AgentManager.get_instance()
        self.task_chains: Dict[str, TaskChain] = {}  # 用于存储不同请求ID的task_chain

        self._initialized = True

    @classmethod
    def get_instance(cls) -> "AgentCommunication":
        """获取AgentCommunication单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def request_agent_assistance(
        self, agent_name: str, arguments: dict, request_id: Optional[str] = None
    ) -> AgentResponse:
        """请求Agent协助"""
        try:
            # 检查现有的TaskChain是否超时，如果超时则移除
            # 这里默认超时时间为10分钟 (600秒)
            current_time = time.time()
            expired_task_chains = []
            for task_id, task_chain in self.task_chains.items():
                # 使用最近活动时间判断过期，避免误清理活跃任务链
                last_active_time = max(task_chain.creation_time, task_chain.last_call_time)
                if current_time - last_active_time > 600:
                    expired_task_chains.append(task_id)
            for task_id in expired_task_chains:
                self.task_chains.pop(task_id, None)

            logger.info(f"开始请求Agent协助: agent_name={agent_name}, arguments={arguments}, request_id={request_id}")

            # 获取或创建对应请求ID的task_chain
            if request_id is not None:
                if request_id not in self.task_chains:
                    self.task_chains[request_id] = TaskChain(request_id=request_id)
                task_chain = self.task_chains[request_id]
            else:
                # 如果request_id为None，创建一个临时的TaskChain
                task_chain = TaskChain(request_id=request_id)

            # 打印任务链信息
            logger.info(
                f"Agent调用 - 消息ID: {request_id}, "
                f"当前循环次数: {task_chain.call_count + 1}, "
                f"最大循环次数: {task_chain.max_loops}"
            )

            # 从arguments中提取task参数
            task = arguments.get("task", "") if arguments else ""

            # 增加调用计数
            task_chain.increment_call_count()

            # 检查是否超过最大调用次数
            try:
                task_chain.check_loop_limit()
            except TaskChain.MaxLoopLimitExceededError as e:
                logger.warning(f"{str(e)}")
                # 从字典中移除已完成的TaskChain
                if request_id is not None:
                    self.task_chains.pop(request_id, None)
                return AgentResponse(result=f"{str(e)}。请重新开始新的任务。")

            # 等待API调用间隔
            await task_chain.wait_api_interval()

            # 调用Agent执行任务
            try:
                response = await self.agent_manager.dispatch_agent_task(agent_name, task)
                task_chain.increment_loop()
                logger.info(f"Agent调用完成: response={response}")

            except Exception as e:
                logger.error(f"Agent调用失败: {e}")
                raise
            logger.info("Agent协助请求完成")
            return response

        except Exception as e:
            logger.error(f"Agent协助请求发生未预期错误: {e}")
            raise

    def reload_configs(self) -> None:
        """重新加载配置"""
        logger.info("重新加载Agent配置")
        self.agent_manager.reload_configs()
        logger.info("Agent配置重新加载完成")
