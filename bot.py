import nonebot
from nonebot.adapters.onebot.v12 import Adapter as Adapterv12
from nonebot.adapters.onebot.v11 import Adapter as Adapterv11
from utils.logger import init_logger

init_logger()

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapterv12)
driver.register_adapter(Adapterv11)

nonebot.load_plugin("nonebot_plugin_muicebot")

nonebot.run()