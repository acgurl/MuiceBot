import random

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from nonebot import logger
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v12 import Message

from .muice import Muice


async def send_message(bot: Bot, **kwargs):
    """
    定时任务：发送信息

    :param bot: 适配器提供的 Bot 类
    **kwargs 中与 bot 交互所需要的参数可参见 https://onebot.adapters.nonebot.dev/docs/api/v12/bot#Bot-send
    """
    probability = kwargs.get("random", 1)
    if not (random.random() < probability):
        return

    logger.info(f"定时任务: send_message: {kwargs.get('message', '')}")

    kwargs.update({"message": Message(kwargs.get("message", ""))})
    await bot.call_api("send_message", **kwargs)


async def model_ask(muice_app: Muice, bot: Bot, prompt: str, **kwargs):
    """
    定时任务：向模型发送消息

    :param muice_app: 沐雪核心类，用于与大语言模型交互
    :param bot: 适配器提供的 Bot 类
    :param prompt: 模型提示词

    **kwargs 中与 bot 交互所需要的参数可参见 https://onebot.adapters.nonebot.dev/docs/api/v12/bot#Bot-send
    """
    probability = kwargs.get("random", 1)
    if not (random.random() < probability):
        return

    logger.info(f"定时任务: model_ask: {prompt}")
    self_info = await bot.call_api("get_self_info")
    self_id = self_info["user_id"]
    self_name = self_info["user_name"]

    if muice_app.model and muice_app.model.is_running:
        message = muice_app.ask(
            prompt,
            self_name,
            self_id,
            kwargs.get("group_id", "-1"),
            enable_history=False,
        )

    kwargs.update({"message": Message(message)})

    await bot.call_api("send_message", **kwargs)


# 读取 YAML 配置文件
def load_config_jobs(file_path="configs.yml") -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("schedule", [])


def setup_scheduler(muice: Muice, bot: Bot) -> AsyncIOScheduler:
    """
    设置任务调度器

    :param muice: 沐雪核心类，用于与大语言模型交互
    """
    jobs = load_config_jobs()
    scheduler = AsyncIOScheduler()

    if not jobs:
        jobs = []

    for job in jobs:
        job_id = job["id"]
        job_type = "send_message" if job.get("message", None) else "model_ask"
        trigger_type = job["trigger"]

        # 解析触发器
        if trigger_type == "cron":
            cron_expr = job["cron"]
            minute, hour, day, month, day_of_week = cron_expr.split()
            trigger = CronTrigger(
                minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
            )

        elif trigger_type == "interval":
            interval_params = job["interval"]
            trigger = IntervalTrigger(**interval_params)

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
                args=[bot],
                kwargs=job,
            )
        else:
            scheduler.add_job(
                model_ask,
                trigger,
                id=job_id,
                replace_existing=True,
                args=[muice, bot, job.get("ask", "")],
                kwargs=job,
            )

        logger.info(f"定时任务 {job_id} 已注册")

    scheduler.start()
    return scheduler
