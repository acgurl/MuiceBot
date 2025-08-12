import asyncio
import time
from typing import Optional

from muicebot.agent.config import agent_plugin_config


class TaskChain:
    """Agent调用计数管理"""

    class MaxLoopLimitExceededError(Exception):
        """超过最大循环限制异常"""

        def __init__(self, max_loops: int):
            self.max_loops = max_loops
            super().__init__(f"调用次数已达到最大限制 {max_loops}")

    def __init__(self, max_loops: Optional[int] = None) -> None:
        self.max_loops = max_loops if max_loops is not None else agent_plugin_config.max_loop_count

        self.current_loop = 0
        self.call_count = 0  # 调用计数器
        self.last_call_time = 0.0  # 上次调用时间

    def increment_loop(self) -> None:
        """增加循环计数"""
        self.current_loop += 1

    def increment_call_count(self) -> None:
        """增加调用计数"""
        self.call_count += 1

    def check_loop_limit(self) -> None:
        """
        检查是否超过循环限制

        Raises:
            MaxLoopLimitExceededError: 当调用次数超过最大限制时抛出
        """
        if self.call_count > self.max_loops:
            raise TaskChain.MaxLoopLimitExceededError(self.max_loops)

    async def wait_api_interval(self) -> None:
        """
        在调用之间添加API调用间隔
        """
        current_time = time.time()
        api_call_interval = agent_plugin_config.api_call_interval

        # 如果不是第一次调用，检查是否需要等待
        if not self.last_call_time == 0.0:
            # 计算距离上次调用的时间
            time_since_last_call = current_time - self.last_call_time
            # 如果距离上次调用的时间小于配置的间隔，则等待
            if time_since_last_call < api_call_interval:
                wait_time = api_call_interval - time_since_last_call
                await asyncio.sleep(wait_time)
        else:
            # 如果是第一次调用，则等待完整的间隔
            await asyncio.sleep(api_call_interval)

        # 更新上次调用时间
        self.last_call_time = time.time()

    def reset(self) -> None:
        """重置调用计数"""
        self.current_loop = 0
        self.call_count = 0
        self.last_call_time = 0.0
