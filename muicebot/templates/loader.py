from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from nonebot import logger

from .model import PromptTemplatesConfig, PromptTemplatesData

SEARCH_PATH = ["./templates", Path(__file__).parent.parent / "builtin_templates"]

TEMPLATES_CONFIG_PATH = "./configs/templates.yml"


def load_templates_config() -> dict:
    """
    获取模板配置
    """
    try:
        with open(TEMPLATES_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def load_templates_data(userid: str, is_private: bool = False) -> PromptTemplatesData:
    """
    获取模板数据
    """
    config = load_templates_config()
    templates_config = PromptTemplatesConfig(**config)
    return PromptTemplatesData.from_config(templates_config, userid=userid, is_private=is_private)


def generate_prompt_from_template(template_name: str, userid: str, is_private: bool = False) -> str:
    """
    获取提示词
    """
    env = Environment(loader=FileSystemLoader(SEARCH_PATH))

    if not template_name.endswith((".j2", ".jinja2")):
        template_name += ".jinja2"
    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        logger.error(f"模板文件 {template_name} 未找到!")
        return ""

    templates_data = load_templates_data(userid, is_private)
    prompt = template.render(templates_data.model_dump())

    return prompt
