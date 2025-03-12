import nonebot
from nonebot.adapters.onebot.v11 import Adapter as Adapterv11
from nonebot.adapters.onebot.v12 import Adapter as Adapterv12
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.telegram import Adapter as TelegramAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapterv12)
driver.register_adapter(Adapterv11)
driver.register_adapter(TelegramAdapter)
driver.register_adapter(QQAdapter)

nonebot.load_plugin("Muice")

nonebot.run()
