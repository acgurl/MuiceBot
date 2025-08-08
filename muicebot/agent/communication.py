from typing import Tuple
from .manager import AgentManager
from .models import AgentResponse

class AgentCommunication:
    """Agent与主模型通信接口"""
    
    def __init__(self):
        self.agent_manager = AgentManager()
        
    async def request_agent_assistance(self, agent_name: str, task: str, userid: str = "", is_private: bool = False) -> str:
        """请求Agent协助"""
        try:
            response = await self.agent_manager.dispatch_agent_task(agent_name, task, userid, is_private)
            result, continue_chain = await self.agent_manager.handle_agent_response(response)
            
            # 处理任务链循环
            loop_count = 0
            max_loops = self.agent_manager.config_manager.get_agent_config(agent_name).max_loop_count
            
            while continue_chain and loop_count < max_loops:
                response = await self.agent_manager.dispatch_agent_task(agent_name, result, userid, is_private)
                result, continue_chain = await self.agent_manager.handle_agent_response(response)
                loop_count += 1
                
            return result
        except Exception as e:
            return f"Agent调用失败: {str(e)}"
            
    def reload_configs(self):
        """重新加载配置"""
        self.agent_manager.reload_configs()