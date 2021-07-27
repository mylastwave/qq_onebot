from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
from nonebot.adapters.cqhttp.message import MessageSegment
from .script import role_img_prod
import os
import random

BOT_PATH = os.getcwd()

@on_command("机动战姬聚变更新", rule=to_me()).handle()
async def _update_jb(bot: Bot, event:Event, state: T_State):
    user_id = event.get_user_id()
    if user_id in bot.config.superusers:
        await role_img_prod()
    await bot.send(event, "机动战姬更新完成！", at_sender=True)

@on_command("十连", rule=to_me()).handle()
async def gacha(bot: Bot, event:Event, state: T_State):
    """
    总共100
    """
    star3 = 85
    star4 = 13
    star5 = 2
    continue_count = 0  # 当前保底池数
    probability_up_std = 50 # 触发概率增加机制最低数量
    star5_probability = 2 + max(continue_count - probability_up_std, 0)  # 五星出货率
    res_list = []   # 随机列表
    for i in range(10):
        res_list.append(random.randint(1, 100))
