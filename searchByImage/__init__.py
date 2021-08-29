from graia.saya import Saya, Channel

from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage, Forward
from graia.application.group import Group
from graia.application.message.elements.internal import *

from collections import OrderedDict
import requests
import json

__name__ = "searchByImage"
__description__ = "调用saucenaoAPI以图搜图"
__author__ = "Jobove"
__usage__ = "在群内发送 以图搜图并在消息内添加图片 即可"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def groupMessageProcessor(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.hasText('以图搜图') and message.has(Image):
        await searchBySaucenao(app, group, message)


async def searchBySaucenao(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    # 获取第一张图片并调用API进行查询
    picture = message.getFirst(Image)
    pictureUrl = picture.url
    pictureUrl = pictureUrl.replace(':', '%3A').replace('/', '%2F')
    requestUrl = 'https://saucenao.com/search.php?db=999&output_type=2&numres=16&url=' + pictureUrl + '&api_key=' + api_key
    results = requests.get(requestUrl)
    results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(results.text)
    available = Plain("API调用余量 30s|24h: " + str(results['header']['short_remaining']) + '|' + str(
        results['header']['long_remaining']))

    if not int(results['header']['user_id']) > 0:
        await app.sendGroupMessage(group, MessageChain.create([Plain("API调用失败, 可能是服务器网络问题, 请稍后再试。")]))
        return

    reply = getProperResults(results)
    reply.append(available)
    reply = MessageChain.create(reply)

    await app.sendGroupMessage(group, reply, quote=message[Source][0])


def getProperResults(results) -> list:
    goodResults = []
    for item in results['results']:
        if float(item['header']['similarity']) >= 80.0:
            if 'ext_urls' not in item['data']:
                continue
            tmp = [float(item['header']['similarity']), item['data']['ext_urls'][0]]
            goodResults.append(tmp)
        else:
            break
    if len(goodResults) == 0:
        reply = [Plain("未在任何来源中寻找到相似度大于80%的结果。")]
        return reply
    return generateReply(goodResults)


def generateReply(goodResults) -> MessageChain:
    reply = []
    if len(goodResults) > 1:
        reply.append(Plain("已在多个来源找到相似度大于80%的结果:\n"))
    else:
        reply.append(Plain("在以下来源找到相似度大于80%的结果:\n"))
    for item in goodResults:
        reply.append(Plain("相似度: {0}, 链接: {1}\n".format(item[0], item[1])))
    return reply


api_key = ''
