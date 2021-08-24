from nonebot import on_request
from nonebot.adapters import Bot, Event
from nonebot.rule import Rule
from nonebot.typing import T_State


async def add_friend_request(bot: "Bot", event: "Event", state: T_State):
    return event.request_type == "friend"

request_friend = on_request(rule=Rule(add_friend_request), block=True)


@request_friend.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if event.get_user_id() in bot.config.superusers:
        approve = True
    else:
        approve = False
    await bot.set_friend_add_request(flag=event.flag, approve=approve)
