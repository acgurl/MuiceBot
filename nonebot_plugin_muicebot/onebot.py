from nonebot import on_message, logger, get_driver, get_adapters, get_bot
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch
from nonebot.adapters import Event
from nonebot.adapters.onebot.v12 import MessageEvent as Onebotv12MessageEvent, Bot as Onebotv12Bot
from nonebot.adapters.onebot.v11 import MessageEvent as Onebotv11MessageEvent, Bot as Onebotv11Bot
from nonebot.adapters.telegram import Event as TelegramEvent, Bot as TelegramBot
from nonebot.adapters.telegram.message import File as TelegramFile
from nonebot.adapters.qq import Event as QQEvent, Bot as QQBot, Message as QQMessage
from nonebot.rule import to_me
from arclet.alconna import Args, Alconna
from .muice import Muice
from .utils import save_image
from .scheduler import setup_scheduler

muice = Muice()
scheduler = None

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

command_load = on_alconna(Alconna(['.', '/'], "load", Args["config_name", str, "model.default"]), priority=10, block=True)

command_schedule = on_alconna(Alconna(['.', '/'], "schedule"), priority=10, block=True)

chat = on_message(priority=100, rule=to_me())

@driver.on_bot_connect
@command_schedule.handle()
async def on_bot_connect():
    global scheduler
    if not scheduler:
        scheduler = setup_scheduler(muice, get_bot())

@driver.on_bot_disconnect
async def on_bot_disconnect():
    global scheduler
    if scheduler:
        scheduler.remove_all_jobs()
        scheduler = None

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
    multimodal_enable = "是" if muice.multimodal else "否"
    await command_status.finish(f'当前模型加载器：{model_loader}\n'
                                f'模型加载器状态：{model_status}\n'
                                f'多模态模型: {multimodal_enable}\n')


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
async def handle_command_load(config: Match[str] = AlconnaMatch("config_name")):
    config_name = config.result
    result = muice.change_model_config(config_name)
    await command_load.finish(result)

@chat.handle()
async def handle_supported_adapters(bot: Onebotv11Bot | Onebotv12Bot | TelegramBot | QQBot,
                    event: Onebotv11MessageEvent | Onebotv12MessageEvent | TelegramEvent | QQEvent):
    message = event.get_message()
    message_text = message.extract_plain_text()
    image_paths = []
    userinfo = {}

    session = event.get_session_id()

    if session.startswith('group_'):
        _, groupid, userid = session.split('_')
    elif session.startswith('private_'):
        _, userid, groupid = session.split('_') + ['-1']
    else:
        groupid, userid = '-1', session


    if isinstance(bot, Onebotv12Bot):
        if muice.multimodal:
            image_file_ids = [m.data["file_id"] for m in message if m.type == "image"]
            for file_id in image_file_ids:
                image_path = await bot.get_file(type='url', file_id=file_id) # Onebot V12
                image_paths.append(image_path)

        userinfo = await bot.get_user_info(user_id=userid)
        username = userinfo.get('user_displayname', userid)

    elif isinstance(bot, Onebotv11Bot):
        if muice.multimodal:
            image_paths = [save_image(m.data["url"], m.data['file'])
                            for m in message
                            if m.type == "image" and 'url' in m.data and 'file' in m.data]
            
        userinfo = await bot.get_stranger_info(user_id=int(userid))
        username = userinfo.get('user_displayname', userid)
    
    elif isinstance(event, TelegramEvent):
        if muice.multimodal:
            image_file_ids = [m.data["file"] for m in message if isinstance(m, TelegramFile)]
            for file_id in image_file_ids:
                file = await bot.get_file(file_id=file_id)
                if not file.file_path:
                    continue
                url = f"https://api.telegram.org/file/bot{bot.bot_config.token}/{file.file_path}"
                filename = file.file_path.split('/')[1]
                image_paths.append(save_image(url, filename))
        
        username = event.chat.username # type: ignore
        # first_name = event.from_.first_name # type: ignore
        # last_name = event.from_.last_name # type: ignore
        # username = f"{first_name if first_name else ''} {last_name if last_name else ''}".strip()
        if not username: # tg特色，姓和名都可能不存在且为 Unknown 类型
            username = userid

    elif isinstance(event, QQEvent):
        if muice.multimodal and isinstance(message, QQMessage):
            image_paths = [save_image(m.data['url'], m.data['url'].split('/')[-1] + '.jpg')
                            for m in message
                            if m.type == "image" and 'url' in m.data]

        username = event.member.nick # type: ignore

    else:
        username = userid

    logger.info(f"Received a message: {message_text}")
    
    if not (message_text or image_paths):
        return
    
    response = muice.ask(message_text, username, userid, groupid=groupid, image_paths=image_paths).strip()

    paragraphs = response.split('\n')

    for index, paragraph in enumerate(paragraphs):
        if index == len(paragraphs) - 1:
            await chat.finish(paragraph)
        await chat.send(paragraph)


@chat.handle()
async def handle_universal_adapters(event: Event):
    message = event.get_plaintext()
    user_id = event.get_user_id()
    logger.info(f"Received a message: {message}")
    
    if not message:
        return
    
    response = muice.ask(message, user_id, user_id, groupid = '-1').strip()

    paragraphs = response.split('\n')

    for index, paragraph in enumerate(paragraphs):
        if index == len(paragraphs) - 1:
            await chat.finish(paragraph)
        await chat.send(paragraph)