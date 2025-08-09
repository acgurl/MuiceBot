from typing import Tuple
from .manager import AgentManager
from .config import AgentResponse
from nonebot import logger

class AgentCommunication:
    """Agent与主模型通信接口"""
    
    def __init__(self):
        self.agent_manager = AgentManager()
        
    async def request_agent_assistance(self, agent_name: str, task: str, userid: str = "", is_private: bool = False) -> str:
        """请求Agent协助"""
        try:
            logger.info(f"开始请求Agent协助: agent_name={agent_name}, task={task}, userid={userid}, is_private={is_private}")
            
            # 调用Agent执行任务
            try:
                response = await self.agent_manager.dispatch_agent_task(agent_name, task, userid, is_private)
                result, continue_chain = await self.agent_manager.handle_agent_response(response)
                logger.info(f"Agent调用完成: result长度={len(result)}")
            except Exception as e:
                logger.error(f"Agent调用失败: {e}")
                return f"Agent调用失败: {str(e)}"
            
            logger.info(f"Agent协助请求完成")
            return result
            
        except Exception as e:
            logger.error(f"Agent协助请求发生未预期错误: {e}")
            return f"Agent调用失败: {str(e)}"
            
    def reload_configs(self):
        """重新加载配置"""
        try:
            logger.info("重新加载Agent配置")
            self.agent_manager.reload_configs()
            logger.info("Agent配置重新加载完成")
        except Exception as e:
            logger.error(f"重新加载Agent配置失败: {e}")