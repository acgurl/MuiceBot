from nonebot import logger

from muicebot.agent.config import AgentConfigManager, AgentResponse
from muicebot.agent.core import Agent
from muicebot.agent.tools import clear_agent_tool_cache


class AgentManager:
    """Agent管理器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config_manager = AgentConfigManager()
        self._agents: dict = {}
        self._initialized = True

    @staticmethod
    def get_instance():
        """获取AgentManager单例实例"""
        return AgentManager()

    async def dispatch_agent_task(self, agent_name: str, task: str) -> AgentResponse:
        """分发任务给指定Agent"""
        logger.info(f"开始分发Agent任务: agent_name={agent_name}, task={task[:50]}...")

        try:
            # 获取或创建Agent实例
            agent = self._get_or_create_agent(agent_name)
            logger.info(f"Agent实例获取/创建成功: {agent_name}")

            # 执行任务
            response = await agent.execute(task)
            logger.info(f"Agent任务执行完成: {agent_name}")

            return response
        except Exception as e:
            logger.error(f"Agent任务分发失败: {e}")
            return AgentResponse(result=f"任务分发失败: {str(e)}")

    def _get_or_create_agent(self, agent_name: str) -> Agent:
        """获取或创建Agent实例"""
        if agent_name not in self._agents:
            logger.info(f"创建新的Agent实例: {agent_name}")
            try:
                config = self.config_manager.get_agent_config(agent_name)
                self._agents[agent_name] = Agent(config, agent_name)
                logger.info(f"Agent实例创建成功: {agent_name}")
            except Exception as e:
                logger.error(f"Agent实例创建失败: {agent_name}, 错误: {e}")
                raise

        logger.debug(f"使用Agent实例: {agent_name}")
        return self._agents[agent_name]

    async def handle_agent_response(self, response: AgentResponse) -> str:
        """处理Agent返回的结果"""
        logger.info("Agent响应处理完成，结果已返回")
        return response.result

    def reload_configs(self):
        """重新加载配置并刷新工具缓存"""
        logger.info("开始重新加载Agent配置...")

        # 重新加载配置
        self.config_manager.reload_configs()

        # 清空已缓存的Agent实例，以便重新创建
        self._agents.clear()

        # 刷新所有Agent的工具缓存
        logger.info("刷新所有Agent的工具缓存...")
        agent_names = self.config_manager.list_agents()
        for agent_name in agent_names:
            # 直接清空工具缓存
            clear_agent_tool_cache(agent_name)
            logger.debug(f"Agent工具缓存清空成功: {agent_name}")

        logger.info("Agent配置和工具缓存重载完成")
