from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.message import Message, MessageSegment
from nonebot.plugin import on_command
from nonebot.rule import to_me
from nonebot.typing import T_State
import time
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import io
import re
import requests
from collections import OrderedDict
import json

# 文件路径操作
project_cwd = Path().cwd()
gocq_path = project_cwd.parent / "gocq"

# 响应器定义
search_chart = on_command("搜图", rule=to_me())

api_key = "2b2f77d57bc327d72d96e7e053162d23a850883b"
minsim = '80!'

@search_chart.handle()
async def search_chart_handle1(bot: Bot, event: Event, state: T_State):
    # try:
    msg = str(event.get_message()).strip()
    find_re = re.findall(r"\[CQ:image.file=(.*?),url=(.*?)\]", str(msg))
    # print("正则匹配：", find_re)
    if find_re:
        state["cq_list"] = find_re

@search_chart.got("cq_list", "请发送你需要搜索的图片")
async def search_chart_got(bot: Bot, event: Event, state: T_State):
    # print(state["cq_list"])
    find_re = re.findall(r"\[CQ:image.file=(.*?),url=(.*?)\]", state['cq_list'])
    if find_re:
        state["cq_list"] = find_re
    else:
        await search_chart.reject("")

@search_chart.handle()
async def search_chart_handle2(bot: Bot, event: Event, state: T_State):
    find_re = state["cq_list"]
    thumbSize = (250, 250)
    image_info = await bot.get_image(file=find_re[0][0])
    # print("图片接收到了", image_info)
    # file_path = Path("E:/Virtualenv/demo/20210819_000940.jpg")
    # print(file_path)
    # image = Image.open(file_path)
    try:
        image = Image.open(gocq_path / image_info["file"])
    except UnidentifiedImageError:
        await search_chart.finish("无法识别图像文件，会话终止")
    image = image.convert('RGB')
    image.thumbnail(thumbSize, resample=Image.ANTIALIAS)
    imageData = io.BytesIO()
    image.save(imageData, format='PNG')

    url = 'http://saucenao.com/search.php?output_type=2&numres=2&minsim=' + \
       minsim+'&db=999&api_key='+api_key

    files = {'file': ("image.png", imageData.getvalue())}

    # async with aiohttp.ClientSession() as session:
    #     resp = await session.post(url, **files)

    resp = requests.post(url, files=files)

    # with open("result.json", mode="w", encoding="utf-8") as f:
    #     f.write(resp.text)

    processResults = True
    while True:
        if resp.status_code != 200:
            if resp.status_code == 403:
                # print('Incorrect or Invalid API Key! Please Edit Script to Configure...')
                await search_chart.finish("搜图秘钥失效了，请联系开发者解决")
            else:
                #generally non 200 statuses are due to either overloaded servers or the user is out of searches
                # print("status code: "+str(resp.status_code))
                await search_chart.finish("搜图API服务器可能超载了，可以等一会再使用")
        else:
            results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp.text)
            if int(results['header']['user_id'])>0:
                #api responded
                print('Remaining Searches 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                if int(results['header']['status'])==0:
                    #search succeeded for all indexes, results usable
                    break
                else:
                    if int(results['header']['status'])>0:
                        #One or more indexes are having an issue.
                        #This search is considered partially successful, even if all indexes failed, so is still counted against your limit.
                        #The error may be transient, but because we don't want to waste searches, allow time for recovery. 
                        # print('API Error. Retrying in 600 seconds...')
                        await search_chart.finish("目前暂时没有匹配到的结果，您可以耐心等待一段时间后再试试")
                    else:
                        #Problem with search as submitted, bad image, or impossible request.
                        #Issue is unclear, so don't flood requests.
                        # print('Bad image or other request error. Skipping in 10 seconds...')
                        processResults = False
                        await search_chart.finish("该图像不能被搜图API识别")
            else:
                #General issue, api did not respond. Normal site took over for this error state.
                #Issue is unclear, so don't flood requests.
                print('Bad image, or API failure. Skipping in 10 seconds...')
                processResults = False
                time.sleep(10)
                break

    if processResults:
        #print(results)
        
        if int(results['header']['results_returned']) > 0:
            #one or more results were returned
            similarity = str(results['results'][0]['header']['similarity'])
            if float(similarity) > float(results['header']['minimum_similarity']):
                print('hit! ' + similarity)

                #get vars to use
                service_name = ''
                illust_id = 0
                member_id = -1
                index_id = results['results'][0]['header']['index_id']
                    
                if index_id == 5 or index_id == 6:
                    #5->pixiv 6->pixiv historical
                    service_name='pixiv'
                    thumbnail = results['results'][0]['header']['thumbnail']
                    menber_name = results['results'][0]['data']['member_name']
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    await bot.send(
                        event, message=Message(
                            f"平台: {service_name}\n相似度: {similarity}\n作者: {menber_name}\n地址: {ext_url}\n") + 
                            MessageSegment.image(file=thumbnail))
                elif index_id == 8:
                    #8->nico nico seiga
                    service_name='seiga'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['seiga_id']
                    await search_chart.finish(f"识图结果为<{service_name}>，请将样例提供给开发者进行完善")
                elif index_id == 10:
                    #10->drawr
                    service_name='drawr'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['drawr_id']
                    await search_chart.finish(f"识图结果为<{service_name}>，请将样例提供给开发者进行完善")
                elif index_id == 11:
                    #11->nijie
                    service_name='nijie'
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['nijie_id']
                    await search_chart.finish(f"识图结果为<{service_name}>，请将样例提供给开发者进行完善")
                elif index_id == 34:
                    #34->da
                    service_name='da'
                    illust_id=results['results'][0]['data']['da_id']
                    await search_chart.finish(f"识图结果为<{service_name}>，请将样例提供给开发者进行完善")
                elif index_id == 12:
                    service_name = "twitter"
                    source: str = results['results'][0]['data']['source']
                    thumbnail = results['results'][0]['header']['thumbnail']
                    split_list = source.replace("https://twitter.com/", "").split("/")
                    author = split_list[0]
                    await bot.send(
                        event, message=Message(
                            f"平台: {service_name}\n相似度: {similarity}\n作者: {author}\n地址: {source}\n") + 
                            MessageSegment.image(file=thumbnail))
                else:
                    #unknown
                    # print('Unhandled Index! Exiting...')
                    await search_chart.finish("识图结果为未标识的平台，需要进行补充")
            else:
                # print('miss... '+str(results['results'][0]['header']['similarity']))
                await search_chart.finish("相似度未达到最低标准，将不返回结果")
                
        else:
            await search_chart.finish("未查询到结果，非常抱歉(ಥ _ ಥ)")

        if int(results['header']['long_remaining'])<1: #could potentially be negative
            await search_chart.finish("很遗憾，今天的机会已经用完了，等明天吧┐(´•_•`)┌ ")
            # time.sleep(6*60*60)
        if int(results['header']['short_remaining'])<1:
            # print('Out of searches for this 30 second period. Sleeping for 25 seconds...')
            # time.sleep(25)
            await search_chart.finish("搜图的频率太高了，先休息一分钟再用吧")