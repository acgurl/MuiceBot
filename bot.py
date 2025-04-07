import importlib
import sys

import nonebot
import yaml
from nonebot.config import Config
from nonebot.drivers import Driver

PLUGINS_CONFIG_PATH = "./configs/plugins.yml"


def load_yaml_config() -> dict:
    """
    插件优先加载 YAML 配置，失败则返回空字典
    """
    try:
        with open(PLUGINS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def load_specified_adapter(driver: Driver, adapter: str):
    """
    加载指定的 Nonebot 适配器
    """
    try:
        module = importlib.import_module(adapter)
        adapter = module.Adapter
        driver.register_adapter(adapter)  # type:ignore
    except ImportError:
        print(f"\33[35m{adapter}不存在，请检查拼写错误或是否已安装该适配器？")
        sys.exit(1)


nonebot.init()

driver = nonebot.get_driver()

yaml_config = load_yaml_config()
env_config = driver.config.model_dump()
final_config = {**env_config, **yaml_config}  # 合并配置，yaml优先
driver.config = Config(**final_config)

enable_adapters: list[str] = final_config.get("enable_adapters", [])

for adapter in enable_adapters:
    load_specified_adapter(driver, adapter)

nonebot.load_plugin("muicebot")

nonebot.run()
