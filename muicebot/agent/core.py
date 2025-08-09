import asyncio
import time
from typing import List, Optional
from ..llm import load_model, ModelRequest
from ..plugin.func_call import get_function_calls
from ..plugin.mcp import get_mcp_list, handle_mcp_tool
from ..templates import generate_prompt_from_template
from .config import AgentConfig, AgentResponse
from .tools import agent_function_call_handler

class Agent:
    """Agent核心类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        # 使用现有的load_model函数加载模型
        self.model = load_model(config)
        self.tools = self._load_tools(config.tools_list)
        self.call_count = 0  # 调用计数器
        self.last_call_time = 0.0  # 上次调用时间
        
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
        from nonebot import logger
        
        # 增加调用计数
        self.call_count += 1
        logger.info(f"Agent开始执行任务: task={task[:50]}..., userid={userid}, is_private={is_private}, 调用次数={self.call_count}")
        logger.info(f"Agent配置: function_call={self.config.function_call}, tools_list={self.config.tools_list}")
        
        # 检查是否超过最大循环次数
        if self.call_count > self.config.max_loop_count:
            logger.warning(f"Agent调用次数已达到最大限制 {self.config.max_loop_count}")
            return AgentResponse(
                result=f"Agent调用次数已达到最大限制 {self.config.max_loop_count}，无法继续调用",
                need_continue=False
            )
        
        # 在调用之间添加API调用间隔
        if self.call_count > 1:  # 第一次调用不需要等待
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.config.api_call_interval:
                wait_time = self.config.api_call_interval - time_since_last_call
                logger.info(f"Agent调用间隔控制: 等待 {wait_time:.2f} 秒")
                await asyncio.sleep(wait_time)
            self.last_call_time = time.time()
        else:
            self.last_call_time = time.time()
        
        # 准备提示词和工具列表
        prompt = self._prepare_prompt(task, userid, is_private)
        tools = self._prepare_tools()
        
        logger.debug(f"Agent提示词准备完成: prompt长度={len(prompt)}")
        logger.debug(f"Agent工具准备完成: 工具数量={len(tools)}")
        
        # 构造模型请求
        model_request = ModelRequest(
            prompt=prompt,
            tools=tools if self.config.function_call else []
        )
        
        logger.info(f"Agent模型请求构造完成，开始调用模型")
        
        # 调用模型
        try:
            response = await self.model.ask(model_request)
            logger.info(f"Agent模型调用完成: succeed={response.succeed}, 响应长度={len(response.text)}")
            logger.debug(f"Agent模型响应内容: {response.text[:200]}...")
        except Exception as e:
            logger.error(f"Agent模型调用失败: {e}")
            return AgentResponse(result=f"模型调用失败: {str(e)}", need_continue=False)
        
        # 解析响应并构造AgentResponse
        try:
            agent_response = self._parse_response(response)
            logger.info(f"Agent响应解析完成: result长度={len(agent_response.result)}, need_continue={agent_response.need_continue}")
            if agent_response.need_continue:
                logger.info(f"Agent请求继续调用: next_agent={agent_response.next_agent}, next_task={agent_response.next_task}")
            return agent_response
        except Exception as e:
            logger.error(f"Agent响应解析失败: {e}")
            return AgentResponse(result=f"响应解析失败: {str(e)}", need_continue=False)
        
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
        from nonebot import logger
        
        result = model_response.text
        logger.debug(f"Agent响应解析完成: 结果长度={len(result)}")
        
        # Agent只返回结果，不决定是否继续调用
        # 继续调用的决定权在muicebot
        return AgentResponse(
            result=result,
            need_continue=False,
            next_agent=None,
            next_task=None
        )