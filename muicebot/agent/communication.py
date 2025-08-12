from nonebot import logger

from muicebot.agent.chain import TaskChain
from muicebot.agent.config import AgentResponse
from muicebot.agent.manager import AgentManager


class AgentCommunication:
    """Agent与主模型通信接口"""

    def __init__(self) -> None:
        self.agent_manager = AgentManager.get_instance()
        self.task_chain = TaskChain()

    async def request_agent_assistance(self, agent_name: str, arguments: dict) -> AgentResponse:
        """请求Agent协助"""
        try:
            logger.info(f"开始请求Agent协助: agent_name={agent_name}, arguments={arguments}")

            # 从arguments中提取task参数
            task = arguments.get("task", "") if arguments else ""

            # 增加调用计数
            self.task_chain.increment_call_count()

            # 检查是否超过最大调用次数
            try:
                self.task_chain.check_loop_limit()
            except TaskChain.MaxLoopLimitExceededError as e:
                logger.warning(f"{str(e)}")
                return AgentResponse(result=f"{str(e)}。请重新开始新的任务。")

            # 等待API调用间隔
            await self.task_chain.wait_api_interval()

            # 调用Agent执行任务
            try:
                response = await self.agent_manager.dispatch_agent_task(agent_name, task)
                self.task_chain.increment_loop()
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
        # 重置调用计数
        self.task_chain.reset()
        logger.info("Agent配置重新加载完成")
