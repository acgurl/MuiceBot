from typing import List, Optional
from .config import AgentResponse

class TaskChain:
    """任务链管理"""
    
    def __init__(self, max_loops: int = 5):
        self.max_loops = max_loops
        self.current_loop = 0
        self.history: List[AgentResponse] = []
        
    def add_response(self, response: AgentResponse):
        """添加响应到历史记录"""
        self.history.append(response)
        
    def should_continue(self) -> bool:
        """判断是否应该继续任务链"""
        if self.current_loop >= self.max_loops:
            return False
            
        if not self.history:
            return False
            
        last_response = self.history[-1]
        return last_response.need_continue
        
    def get_next_task(self) -> Optional[tuple[str, str]]:
        """获取下一个任务"""
        if not self.history:
            return None
            
        last_response = self.history[-1]
        if last_response.need_continue and last_response.next_agent and last_response.next_task:
            return (last_response.next_agent, last_response.next_task)
            
        return None
        
    def increment_loop(self):
        """增加循环计数"""
        self.current_loop += 1
        
    def reset(self):
        """重置任务链"""
        self.current_loop = 0
        self.history.clear()
        
    def get_final_result(self) -> str:
        """获取最终结果"""
        if self.history:
            return self.history[-1].result
        return ""