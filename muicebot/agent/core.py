from typing import List, Optional
from ..llm import load_model, ModelRequest
from ..plugin.func_call import get_function_calls
from ..plugin.mcp import get_mcp_list, handle_mcp_tool
from ..templates import generate_prompt_from_template
from .models import AgentConfig, AgentResponse
from .tools import agent_function_call_handler

class Agent:
    """Agent核心类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        # 使用现有的load_model函数加载模型
        self.model = load_model(config)
        self.tools = self._load_tools(config.tools_list)
        
    def _load_tools(self, tools_list: List[str]) -> List[dict]:
        """加载Agent可调用的工具"""
        available_tools = []
        
        # 获取Function Call工具
        function_calls = get_function_calls()
        for tool_name in tools_list:
            if tool_name in function_calls:
                available_tools.append(function_calls[tool_name].data())
                
        # 获取MCP工具
        try:
            mcp_tools = get_mcp_list()
            for tool in mcp_tools:
                # 检查工具名称是否在配置的工具列表中
                if tool.get("function", {}).get("name") in tools_list:
                    available_tools.append(tool)
        except Exception:
            # 如果MCP工具加载失败，继续使用Function Call工具
            pass
            
        return available_tools
        
    async def execute(self, task: str, userid: str = "", is_private: bool = False) -> AgentResponse:
        """执行任务"""
        # 准备提示词和工具列表
        prompt = self._prepare_prompt(task, userid, is_private)
        tools = self._prepare_tools()
        
        # 构造模型请求
        model_request = ModelRequest(
            prompt=prompt,
            tools=tools if self.config.function_call else []
        )
        
        # 调用模型
        response = await self.model.ask(model_request)
        
        # 解析响应并构造AgentResponse
        return self._parse_response(response)
        
    def _prepare_prompt(self, task: str, userid: str, is_private: bool) -> str:
        """准备提示词"""
        if self.config.template:
            system_prompt = generate_prompt_from_template(self.config.template, userid, is_private).strip()
            return f"{system_prompt}\n\n{task}"
        return task
        
    def _prepare_tools(self) -> List[dict]:
        """准备工具列表"""
        # 工具已经加载在self.tools中
        return self.tools
        
    def _parse_response(self, model_response) -> AgentResponse:
        """解析模型响应"""
        # 简单实现，实际可能需要更复杂的解析逻辑
        return AgentResponse(result=model_response.text)