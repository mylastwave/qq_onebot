import pymongo
import json
import asyncio
import os
from .script import role_info_spider

# BOT_PATH = os.path.dirname(__file__)
BOT_PATH = os.getcwd()

CACHE_PATH = "/data/cache/jdzj_jb/"

JSON_PATH = "/data/json/jdzj_jb/"

ROLE_PATH = "/data/images/jdzj_jb/role/"

OFFILE_WEB = "https://wiki.biligame.com/ag/首页"

ROLE_TB = "https://wiki.biligame.com/ag/战姬筛选表"

role_name_db_field = "名字"

def update_role_info_to_db():
    """
    从role_info.json中更新数据到数据库
    """
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    jb_db = myclient["jdzj_jb"]
    jb_col = jb_db["role_info"]
    if not os.path.exists(BOT_PATH + JSON_PATH + "role_info.json"):
        asyncio.run(role_info_spider())
    with open(BOT_PATH + JSON_PATH + "role_info.json", encoding="utf-8") as f:
        role_info_str = f.read()
    role_info_list = json.loads(role_info_str)
    for i in role_info_list:
        col_filter = {role_name_db_field: i[role_name_db_field]}
        jb_col.find_one_and_delete(col_filter)
        jb_col.insert_one(i)

def find_star_role_name_list(star: str):
    """
    查找指定星级的角色名字的列表
    """
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    jb_db = myclient["jdzj_jb"]
    jb_col = jb_db["role_info"]
    cols = jb_col.find({"星级": star}, {"_id": 0, role_name_db_field: 1, "星级": 1})
    result = [i[role_name_db_field] for i in cols]
    return result

async def redis(): ...

if __name__ == "__main__":
    result = asyncio.run(find_star_role_name_list("3"))
    print(result)