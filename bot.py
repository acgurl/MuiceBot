import nonebot
from nonebot.adapters.onebot.v12 import Adapter
from utils.logger import init_logger

init_logger()

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

nonebot.load_plugin("nonebot_plugin_muicebot")

nonebot.run()