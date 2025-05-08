import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import get_bot, logger
from nonebot_plugin_alconna.uniseg import Target, UniMessage

from .config import get_schedule_configs
from .models import Message
from .muice import Muice


async def send_message(target_id: str, message: str, probability: float = 1):
    """
    定时任务：发送信息

    :param target_id: 目标id；若为群聊则为 group_id 或者 channel_id，若为私聊则为 user_id
    :param message: 要发送的消息
    :param probability: 发送几率
    """
    if not (random.random() < probability):
        return

    logger.info(f"定时任务: send_message: {message}")

    target = Target(target_id)
    await UniMessage(message).send(target=target, bot=get_bot())


async def model_ask(muice_app: Muice, target_id: str, prompt: str, probability: float = 1):
    """
    定时任务：向模型发送消息

    :param muice_app: 沐雪核心类，用于与大语言模型交互
    :param target_id: 目标id；若为群聊则为 group_id 或者 channel_id，若为私聊则为 user_id
    :param prompt: 模型提示词
    :param probability: 发送几率
    """
    if not (random.random() < probability):
        return

    logger.info(f"定时任务: model_ask: {prompt}")

    if muice_app.model and muice_app.model.is_running:
        message = Message(message=prompt, userid=f"(bot_ask){target_id}")
        response = await muice_app.ask(message, enable_history=False, enable_plugins=False)

        target = Target(target_id)
        await UniMessage(response.text).send(target=target, bot=get_bot())


def setup_scheduler(muice: Muice) -> AsyncIOScheduler:
    """
    设置任务调度器

    :param muice: 沐雪核心类，用于与大语言模型交互
    """
    jobs = get_schedule_configs()
    scheduler = AsyncIOScheduler()

    for job in jobs:
        job_id = job.id
        job_type = "send_message" if job.say else "model_ask"
        trigger_type = job.trigger
        trigger_args = job.args

        # 解析触发器
        if trigger_type == "cron":
            trigger = CronTrigger(**trigger_args)

        elif trigger_type == "interval":
            trigger = IntervalTrigger(**trigger_args)

        else:
            logger.error(f"未知的触发器类型: {trigger_type}")
            continue

        # 添加任务
        if job_type == "send_message":
            scheduler.add_job(
                send_message,
                trigger,
                id=job_id,
                replace_existing=True,
                args=[job.target, job.say, job.probability],
            )
        else:
            scheduler.add_job(
                model_ask,
                trigger,
                id=job_id,
                replace_existing=True,
                args=[muice, job.target, job.ask, job.probability],
            )

        logger.success(f"已注册定时任务: {job_id}")

    if jobs:
        scheduler.start()
    return scheduler
