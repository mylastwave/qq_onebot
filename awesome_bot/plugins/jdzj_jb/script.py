from re import I
from time import time_ns
import aiohttp
import os
from bs4 import BeautifulSoup
import bs4
import json
from PIL import Image
import cv2
import asyncio
import base64

"""
维多利亚 第一张 品质背景 第二张 头像 第三张 品质框 第四章 星级
辛迪 第一张 品质背景 第二张 头像 第三张 品质框 第四张 属性类型框 第五张 属性职业图标 第六张 星级
品质背景    头像                   品质框                     属性类型框         属性职业图标       星级 
[名字] | [名字].png | Icon160 quality frame [星级].png | [属性]图标背景.png | [属性][兵种].png | [星级].png
  布鲁 |  布鲁.png  |  Icon160 quality frame 3.png     |  热熔图标背景.png  |   热熔强袭.png   |  3星.png
"""

# BOT_PATH = os.path.dirname(__file__)
BOT_PATH = os.getcwd().replace("\\", "/")

CACHE_PATH = "/data/cache/jdzj_jb/"
JSON_PATH = "/data/json/jdzj_jb/"
ROLE_PATH = "/data/images/jdzj_jb/role/"
ZM_BJ_PATH = "/data/images/jdzj_jb/zm_bj/"
OFFILE_WEB = "https://wiki.biligame.com/ag/首页"
ROLE_TB = "https://wiki.biligame.com/ag/战姬筛选表"

async def role_info_spider():
    """
    爬取wiki筛选表获取角色信息
    """
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(ROLE_TB, headers=header) as res:
            soup = BeautifulSoup(await res.text(), features="lxml")

    is_tb_head = True
    tb_head = []
    role_info = []

    for child in soup.find("table", attrs={"id": "CardSelectTr"}).tbody.children:
        if type(child) == bs4.element.Tag:
            # print(list(child.stripped_strings))
            string_lis = []
            for i in child.descendants:
                if type(i) == bs4.element.Tag:
                    if i.string:
                        string_lis.append(i.string.replace("\n", ""))
            # print(string_lis)
            if is_tb_head:
                tb_head = string_lis[1:]
                is_tb_head = False
            else:
                prop_dict = {}
                for prop_head, prop in zip(tb_head, string_lis):
                    prop_dict[prop_head] = prop
                role_info.append(prop_dict)

    role_info_json = json.dumps(role_info, ensure_ascii=False)
    if not os.path.isdir(BOT_PATH + JSON_PATH[: -1]):
        os.makedirs(BOT_PATH + JSON_PATH[: -1])
    with open(BOT_PATH + JSON_PATH + "role_info.json", "w", encoding="utf-8") as f:
        f.write(role_info_json)
    return True

async def role_img_spider():
    """
    爬取wiki首页角色头像框的组成图片
    """
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(OFFILE_WEB, headers=header) as res:
            soup = BeautifulSoup(await res.text(), features="lxml")
    popups = soup.find_all("span", attrs={"class": "popup"})

    for popup in popups:
        role = popup.select("font")[0].string
        imgs = popup.select("img")
        # print(role)
        for img in imgs:
            alt = img.attrs.get("alt")
            src = img.attrs.get("src")
            if alt == role:
                img_name = src[-8:]
            elif "Spr AG" in alt:
                img_name = role + ".png"
            else:
                img_name = alt
            
            await img_dl(src, img_name, header)
        
async def img_dl(url, img_name, header):
    """
    下载图片
    :param url:角色名称
    :param img_name:图片名字
    :param header:请求头
    """
    if not os.path.isdir(BOT_PATH + CACHE_PATH[: -1]):
        os.makedirs(BOT_PATH + CACHE_PATH[: -1])
    file_name = BOT_PATH + CACHE_PATH + imgname_to_base64(img_name.replace(".png", "")) + ".png"
    if os.path.exists(file_name):
        # print(file_name, "已存在")
        return
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as img:
                f = open(file_name, mode="wb")
                f.write(await img.read())
                f.close()

def imgname_to_base64(string: str):   return base64.b64encode(string.encode()).decode().replace("/", "-")

async def headportrait(role_name, star, attri, prof):
    """
    合成头像图标
    :param role_name:角色名称
    :param star:星级
    :param attri:属性
    :param prof:职业定位
    """
    # role_name = "康纳"
    # star = 3
    # attri = "电磁"
    # prof = "强袭"
    if not (role_name and star and attri and prof):
        return
    # print(role_name, star, attri, prof)
    # 角色头像贴在颜色背景上
    img_bg = Image.open(BOT_PATH + CACHE_PATH + imgname_to_base64("bg_{}".format(star)) + ".png")
    img_bg.convert("RGBA")
    overlap_img = img_bg.crop((11, 9, 97, 95))
    del img_bg
    img_role_path = BOT_PATH + CACHE_PATH + imgname_to_base64(role_name) + ".png"
    if not os.path.exists(img_role_path):
        return
    img_role = Image.open(img_role_path)
    img_role.convert("RGBA")
    overlap_img.paste(img_role, (0, 0), img_role)
    # 品级框贴在重叠图片上
    img_frame = Image.open(BOT_PATH + CACHE_PATH + imgname_to_base64("Icon160 quality frame {}".format(star)) + ".png")
    img_frame.convert("RGBA")
    img_frame = img_frame.crop((13, 10, 107, 104))
    # img_frame.show()
    blank_bg = Image.new("RGBA", img_frame.size, (0, 0, 0, 0))
    x, y = int((img_frame.width - overlap_img.width) / 2), int((img_frame.height - overlap_img.height) / 2)
    box = (x, y, x + overlap_img.width, y + overlap_img.height)
    blank_bg.paste(overlap_img, box)
    blank_bg.paste(img_frame, (0, 0), img_frame)
    # blank_bg.save(BOT_PATH + "/data/images/jdzj_jb/test/{}.png".format(role_name))
    # blank_bg.show()
    # img_frame = img_frame.resize(overlap_img.size)
    # overlap_img.paste(img_frame, (0, 0), img_frame)
    # overlap_img.show()
    # 星级贴在重叠图片上
    overlap_img = blank_bg.copy().resize((100, 100))
    del blank_bg
    img_star = Image.open(BOT_PATH + CACHE_PATH + imgname_to_base64("{}星".format(star)) + ".png")
    # blank_bg = Image.new("RGBA", (overlap_img.width, img_star.height), (0, 0, 0, 0))
    blank_bg = Image.new("RGBA", overlap_img.size, (0, 0, 0, 0))
    # print(blank_bg.size, img_star.size)
    x = int((blank_bg.width - img_star.width) / 2)
    blank_bg.paste(img_star, (x, blank_bg.height - img_star.height, x + img_star.width, blank_bg.height), img_star)
    overlap_img.paste(blank_bg, (0, 0), blank_bg)
    # overlap_img.show()
    # 重叠属性职业图标和属性框
    img_attri = Image.open(BOT_PATH + CACHE_PATH + imgname_to_base64(attri + "图标背景") + ".png")
    img_prof = Image.open(BOT_PATH + CACHE_PATH + imgname_to_base64(attri + prof) + ".png")
    img_attri.paste(img_prof, (0, 0), img_prof)
    img_attri = img_attri.crop((5, 6, 25, 26))
    # img_attri.show()
    # 将职业属性图标粘贴到重叠头像上
    blank_bg = Image.new("RGBA", (overlap_img.width + 5, overlap_img.height), (0, 0, 0, 0))
    blank_bg.paste(overlap_img, (0, 0, overlap_img.width, overlap_img.height))
    x, y = overlap_img.width - 15, overlap_img.height - 20 - 20
    blank_bg.paste(img_attri, (x, y, x + img_attri.width, y + img_attri.height))
    final_img = blank_bg
    # final_img.show()
    if not os.path.isdir(BOT_PATH + ROLE_PATH[: -1]):
        os.makedirs(BOT_PATH + ROLE_PATH[: -1])
    if os.path.exists(BOT_PATH + ROLE_PATH + "{}.png".format(role_name)):
        return
    # cv2.imwrite(BOT_PATH + ROLE_PATH + "{}.png".format(imgname_to_base64(role_name)), final_img)
    final_img.save(BOT_PATH + ROLE_PATH + "{}.png".format(role_name))

async def role_img_prod():
    """
    爬虫和头像合成总api
    """
    await asyncio.gather(*[role_info_spider(), role_img_spider(),])
    with open(BOT_PATH + JSON_PATH + "role_info.json", encoding="utf-8") as f:
        role_info_list = json.loads(f.read())
        await asyncio.gather(*[headportrait(i["名字"], i["星级"], i["核心"], i["类型"]) for i in role_info_list]) 

async def gacha_pic(role_list: list, star: int, user_id: str) -> str:
    """
    抽卡结果展示
    返回 图片名称
    """
    if star == 5:
        img_bg = Image.open(BOT_PATH + ZM_BJ_PATH + "zhaomu_04_bg.png") \
        .resize(((105 + 5) * 8, (100 + 10) * 4))
    else:
        img_bg = Image.open(BOT_PATH + ZM_BJ_PATH + "zhaomu_03_bg.png") \
        .resize(((105 + 5) * 8, (100 + 10) * 4))
    img_bg.convert("RGBA")
    for i in range(len(role_list)):
        img_role = Image.open(BOT_PATH + ROLE_PATH + f"{role_list[i]}.png")
        img_bg.paste(img_role, ((img_role.width + 10) * (i % 5 + 1) + 50, (img_role.height + 20) * (i // 5 + 1)), img_role)
    # img_bg.show()
    file_path =  BOT_PATH + CACHE_PATH + user_id + str(time_ns())+ ".png"
    img_bg.save(file_path)
    return file_path
    

if __name__=="__main__":
    asyncio.run(role_info_spider())
