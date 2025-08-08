import yaml
from pathlib import Path
from typing import Dict, List
from .models import AgentConfig

AGENTS_CONFIG_PATH = Path("configs/agents.yml")

class AgentConfigManager:
    """Agent配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, AgentConfig] = {}
        self._load_configs()
        
    def _load_configs(self):
        """加载Agent配置文件"""
        if not AGENTS_CONFIG_PATH.exists():
            # 如果配置文件不存在，创建一个默认的Agent配置
            AGENTS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "assistant": {
                    "function_call": True,
                    "stream": False,
                    "multimodal": False,
                    "api_host": "",
                    "api_key": "",
                    "tools_list": []
                }
            }
            with open(AGENTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)
            # 加载默认配置
            self._configs["assistant"] = AgentConfig(**default_config["assistant"])
            return
            
        with open(AGENTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            configs_dict = yaml.safe_load(f)
            
        if not configs_dict:
            # 如果配置文件为空，创建一个默认的Agent配置
            default_config = {
                "assistant": {
                    "function_call": True,
                    "stream": False,
                    "multimodal": False,
                    "api_host": "",
                    "api_key": "",
                    "tools_list": []
                }
            }
            with open(AGENTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)
            # 加载默认配置
            self._configs["assistant"] = AgentConfig(**default_config["assistant"])
            return
            
        for name, config in configs_dict.items():
            # 设置默认值
            if 'function_call' not in config:
                # 默认启用工具调用
                config['function_call'] = True
                
            if 'stream' not in config:
                # 默认不使用流式输出
                config['stream'] = False
                
            if 'multimodal' not in config:
                # 默认不使用多模态
                config['multimodal'] = False
                
            if 'api_host' not in config:
                # 默认API主机为空
                config['api_host'] = ""
                
            if 'api_key' not in config:
                # 默认API密钥为空
                config['api_key'] = ""
                
            if 'tools_list' not in config or config['tools_list'] is None:
                # 默认工具列表为空列表
                config['tools_list'] = []
                
            # 继承ModelConfig的字段并添加Agent特有的字段
            self._configs[name] = AgentConfig(**config)
            
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """获取指定Agent的配置"""
        if agent_name not in self._configs:
            raise ValueError(f"Agent配置不存在: {agent_name}")
        return self._configs[agent_name]
        
    def list_agents(self) -> List[str]:
        """列出所有Agent"""
        return list(self._configs.keys())
        
    def reload_configs(self):
        """重新加载配置文件"""
        self._configs.clear()
        self._load_configs()
        
    def can_use_tools(self, agent_name: str) -> bool:
        """
        检查Agent是否可以使用工具
        工具调用的逻辑：
        1. 必须启用工具调用(function_call=True)
        2. 工具列表不能为空
        """
        if agent_name not in self._configs:
            return False
            
        config = self._configs[agent_name]
        # 检查是否启用工具调用且工具列表不为空
        return config.function_call and len(config.tools_list) > 0
        
    def get_available_tools(self, agent_name: str) -> List[str]:
        """
        获取Agent可用的工具列表
        """
        if agent_name not in self._configs:
            return []
            
        config = self._configs[agent_name]
        # 只有在启用工具调用时才返回工具列表
        if config.function_call:
            return config.tools_list
        else:
            return []