from typing import Optional
from .config import AgentConfigManager
from .core import Agent
from .models import AgentResponse, AgentConfig

class AgentManager:
    """Agent管理器"""
    
    def __init__(self):
        self.config_manager = AgentConfigManager()
        self._agents: dict = {}
        
    async def dispatch_agent_task(self, agent_name: str, task: str, userid: str = "", is_private: bool = False) -> AgentResponse:
        """分发任务给指定Agent"""
        # 获取或创建Agent实例
        agent = self._get_or_create_agent(agent_name)
        
        # 执行任务
        response = await agent.execute(task, userid, is_private)
        
        return response
        
    def _get_or_create_agent(self, agent_name: str) -> Agent:
        """获取或创建Agent实例"""
        if agent_name not in self._agents:
            config = self.config_manager.get_agent_config(agent_name)
            self._agents[agent_name] = Agent(config)
        return self._agents[agent_name]
        
    async def handle_agent_response(self, response: AgentResponse) -> tuple[str, bool]:
        """处理Agent返回的结果"""
        # 根据Agent响应决定是否继续任务链
        if response.need_continue and response.next_agent and response.next_task:
            # 需要继续调用其他Agent
            next_response = await self.dispatch_agent_task(
                response.next_agent, 
                response.next_task
            )
            return next_response.result, True
        else:
            # 任务链结束
            return response.result, False
            
    def reload_configs(self):
        """重新加载配置"""
        self.config_manager.reload_configs()
        # 清空已缓存的Agent实例，以便重新创建
        self._agents.clear()