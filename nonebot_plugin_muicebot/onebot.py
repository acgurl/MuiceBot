from nonebot import on_message
from nonebot import logger, get_driver, get_adapters
from nonebot.adapters import Event, Message
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch
from nonebot.adapters.onebot.v12 import PrivateMessageEvent, GroupMessageEvent, Bot
from nonebot.rule import to_me
from arclet.alconna import Args, Option, Alconna, Arparma, MultiVar, Subcommand
from .muice import Muice

muice = Muice()

driver = get_driver()
adapters = get_adapters()

@driver.on_startup
async def on_startup():
    if not muice.load_model():
        logger.error("模型加载失败，请检查配置项是否正确")
        exit(1)
    logger.info("MuiceAI 聊天框架已开始运行⭐")

command_help = on_alconna(Alconna(['.', '/'], "help"), priority=90, block=True)

command_status = on_alconna(Alconna(['.', '/'], "status"), priority=90, block=True)

command_reset = on_alconna(Alconna(['.', '/'], "reset"), priority=10, block=True)

command_refresh = on_alconna(Alconna(['.', '/'], "refresh"), priority=10, block=True)

command_undo = on_alconna(Alconna(['.', '/'], "undo"), priority=10, block=True)

command_load = on_alconna(Alconna(['.', '/'], "load", Args["config_name", str, "model"]), priority=10, block=True)

chat = on_message(priority=100, rule=to_me())


@command_help.handle()
async def handle_command_help():
    await command_help.finish('基本命令：\n'
    'help 输出此帮助信息\n'
    'status 显示当前状态\n'
    'refresh 刷新模型输出\n'
    'reset 清空对话记录\n'
    'undo 撤回上一个对话\n'
    'load <config_name> 加载模型\n'
    '（支持的命令前缀：“.”、“/”）')

@command_status.handle()
async def handle_command_status():
    model_loader = muice.model_loader
    model_status = "运行中" if muice.model and muice.model.is_running else "未启动"
    await command_status.finish(f'当前模型加载器：{model_loader}\n'
                                f'模型加载器状态：{model_status}')


@command_reset.handle()
async def handle_command_reset(event: Event):
    userid = event.get_user_id()
    response = muice.reset(userid)
    await command_reset.finish(response)

@command_refresh.handle()
async def handle_command_refresh(event: Event):
    userid = event.get_user_id()
    response = muice.refresh(userid)

    paragraphs = response.split('\n')

    for index, paragraph in enumerate(paragraphs):
        if index == len(paragraphs) - 1:
            await chat.finish(paragraph)
        await chat.send(paragraph)

@command_undo.handle()
async def handle_command_undo(event: Event):
    userid = event.get_user_id()
    response = muice.undo(userid)
    await command_undo.finish(response)

@command_load.handle()
async def handle_test3(config: Match[str] = AlconnaMatch("config_name")):
    config_name = config.result
    muice.change_model_config(config_name)
    await command_load.finish('已成功切换模型配置文件！')

@chat.handle()
async def handle_onebot(bot: Bot, event: PrivateMessageEvent | GroupMessageEvent):
    message = event.get_plaintext()
    session = event.get_session_id()

    if session.startswith('group_'):
        _, groupid, userid = session.split('_')
    else:
        groupid, userid = '-1', session

    userinfo = await bot.get_user_info(user_id=userid)
    username = userinfo.get('user_displayname')
    logger.info(f"Received a message: {message}")
    
    if not message:
        return
    
    response = muice.ask(message, username, userid, groupid=groupid).strip()

    paragraphs = response.split('\n')

    for index, paragraph in enumerate(paragraphs):
        if index == len(paragraphs) - 1:
            await chat.finish(paragraph)
        await chat.send(paragraph)

@chat.handle()
async def handle_general(event: Event):
    message = event.get_plaintext()
    user_id = event.get_user_id()
    logger.info(f"Received a message: {message}")
    
    if not message:
        return
    
    response = muice.ask(message, user_id, user_id, groupid = '-1')

    await chat.finish(response)