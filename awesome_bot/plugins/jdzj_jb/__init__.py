from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
from nonebot.adapters.cqhttp.message import MessageSegment
from .script import role_img_prod, gacha_pic
import os
import random
from .config import Config as JdzjJbConfig
from pathlib import Path

jdzj_jb_config = JdzjJbConfig()

BOT_PATH = os.getcwd()

jb_update_command = on_command(
    "机动战姬聚变更新", rule=to_me(), permission=SUPERUSER, priority=5)
gacha_command = on_command("十连", rule=to_me(), priority=5)


@jb_update_command.handle()
async def update_jb(bot: Bot, event: Event, state: T_State):
    # user_id = event.get_user_id()
    # if user_id in bot.config.superusers:
    await bot.send(event, "机动战姬正在更新……")
    await role_img_prod()
    await bot.send(event, "机动战姬更新完成！")


@gacha_command.handle()
async def gacha(bot: Bot, event: Event, state: T_State):
    """
    十连
    """
    star4_probability = 13
    no_5_count = 0  # 累计不是5星的次数
    probability_up_min_value = 50  # 概率增加机制最低值
    star5_probability = 2 + 2 * \
        max(no_5_count - probability_up_min_value, 0)  # 五星出货率
    res_list = []   # 随机列表
    for _ in range(10):
        random_value = random.randint(1, 100)
        if random_value > star5_probability + star4_probability:
            res_list.append(3)
            no_5_count += 1
        elif random_value > star5_probability:
            res_list.append(4)
            no_5_count += 1
        else:
            res_list.append(5)
            no_5_count = 0
        star5_probability = 2 + 2 * \
            max(no_5_count - probability_up_min_value, 0)
    if res_list.count(3) == len(res_list):
        res_list[-1] = 4
    role_list = []
    for i in res_list:
        if i == 3:
            role_list.append(jdzj_jb_config.star_3_roles[random.randint(
                0, len(jdzj_jb_config.star_3_roles) - 1)])
        elif i == 4:
            role_list.append(jdzj_jb_config.star_4_roles[random.randint(
                0, len(jdzj_jb_config.star_4_roles) - 1)])
        else:
            role_list.append(jdzj_jb_config.star_5_roles[random.randint(
                0, len(jdzj_jb_config.star_5_roles) - 1)])
    # await bot.send(event, " ".join(map(str, role_list)))
    star = 5 if res_list.count(5) else 4
    file_path: str = await gacha_pic(role_list, star, event.get_user_id())
    file_uri = Path(file_path).as_uri()
    # file_path = file_path.split(".")[0] + ".jpg"
    try:
        # await gacha_command.finish(MessageSegment("image", {"file": file_path}))
        await bot.send(event, MessageSegment.image(file_uri))
    except Exception as e:
        print("错误信息：", e)
    finally:
        os.remove(file_path)
