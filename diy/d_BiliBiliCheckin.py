#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# B站Cookie，可设置多个Cookie，Cookie之间用 & 隔开，如果Cookie里有特殊字符请转义
BiliBiliCookie=""

# 投币数量，默认为0
BiliBiliCoin=""

# 投币方式，0为指定分区投币，1为指定UP主投币，默认为0
BiliBiliType=""

# 指定分区投币，可选分区如下，可指定多个分区，分区之间用 & 隔开，默认分区为全部
# 全部 动漫 游戏 电竞 鬼畜 时尚 音乐 科技 数码 知识 动物圈 美食
# 虚拟UP主 明星 舞蹈 生活 综艺 电影 电视剧 相声 特摄 运动 星海 
BiliBiliRegion=""

# 指定UP主投币，可指定多个UP主uid，uid之间用 & 隔开
BiliBiliUP=""

cron: 30 7 * * *
new Env('哔哩哔哩-签到');
"""

from time import sleep
import requests,json,os,random
from datetime import datetime

List = []

# 用户信息
def get_nav(session):
    url = "https://api.bilibili.com/x/web-interface/nav"
    ret = session.get(url=url).json()
    uname = ret["data"]["uname"] # 用户名
    is_login = ret["data"]["isLogin"] # 登录状态
    coin = ret["data"]["money"] # 硬币数量
    current_level = ret["data"]["level_info"]["current_level"] # 当前等级
    current_exp = ret["data"]["level_info"]["current_exp"] # 经验值
    next_exp = ret["data"]["level_info"]["next_exp"] # 下一等级所需经验值
    return uname,is_login,coin,current_level,current_exp,next_exp

# 获取今日已投币数量
def get_coin(session):
    url = "https://api.bilibili.com/x/member/web/coin/log"
    ret = session.get(url=url).json()["data"]["list"]
    starttime = datetime.strptime(str(datetime.now().date())+'0:00:00','%Y-%m-%d%H:%M:%S')
    endtime = datetime.strptime(str(datetime.now().date())+'23:59:59','%Y-%m-%d%H:%M:%S')
    delta = 0
    for x in ret:
        initDate = datetime.strptime(x["time"],'%Y-%m-%d %H:%M:%S')
        if initDate >= starttime and initDate <= endtime:
            delta += x["delta"]
    return 1-delta

# 获取指定up主空间视频投稿信息
def space_arc_search(session,uid:int,pn:int=1,ps:int=30,tid:int=0,order:str="pubdate",keyword:str=""):
    params = {
        "mid": uid, # id int UP主uid
        "pn": pn, # pn int 页码，默认第一页
        "Ps": ps, # ps int 每页数量，默认50
        "tid": tid, # tid int 分区 默认为0(所有分区)
        "order": order, # order str 排序方式，默认pubdate
        "keyword": keyword, # keyword str 关键字，默认为空
    }
    url = "https://api.bilibili.com/x/space/arc/search"
    ret = session.get(url=url, params=params).json()
    return ret["data"]["list"]["vlist"]

# 获取B站分区视频信息
def get_region(session,regionid):
    url = "https://api.bilibili.com/x/web-interface/web/channel/category/channel_arc/list?id="+regionid
    ret = session.get(url=url).json()
    data_list = [
        {
            "aid": one["id"],
            "bvid": one["bvid"],
            "title": one["title"],
        }
        for one in ret["data"]["archive_channels"][0]["archives"]
    ]
    return data_list

# 给指定av号视频投币
def coin_add(session,bili_jct,aid:int,num:int=1,select_like:int=1):
    url = "https://api.bilibili.com/x/web-interface/coin/add"
    post_data = {
        "aid": aid, # aid int 视频av号
        "multiply": num, # num int 投币数量
        "select_like": select_like, # select_like int 是否点赞
        "cross_domain": "true",
        "csrf": bili_jct,
    }
    ret = session.post(url=url, data=post_data).json()
    return ret

# 分享指定av号视频
def share_task(session,bili_jct,aid):
    url = "https://api.bilibili.com/x/web-interface/share/add"
    post_data = {
        "aid": aid, # aid int 视频av号
        "csrf": bili_jct
    }
    ret = session.post(url=url, data=post_data).json()
    return ret

# B站上报视频观看进度
def report_task(session,bili_jct,aid:int,bvid:int,progres:int=300):
    url = "https://api.bilibili.com/x/player/pagelist?bvid="+bvid
    cid = session.get(url=url).json()["data"][0]["cid"]
    urls = "http://api.bilibili.com/x/v2/history/report"
    post_data = {
        "aid": aid, # aid int 视频av号
        "cid": cid, # cid int 视频cid号
        "progres":progres, # progres int 观看秒数
        "csrf": bili_jct
    }
    ret = session.post(url=urls, data=post_data).json()
    return ret

# 企业微信推送
def push(title,content):
    # 获得access_token
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + corpsecret
    re = requests.get(url).json()
    access_token = re['access_token']
    url1 = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="+ access_token
    data = {
       "touser" : touser,
       "msgtype" : "news",
       "agentid" : agentid,
       "news" : {
       "articles" : [{
               "title" : title,
               "description" : content,
            }]
        }
    }
    # 字符串格式
    re1 = requests.post(url=url1, data=json.dumps(data)).json()
    if re1['errcode'] == 0:
        print("推送成功")
    else:
        print("推送失败")

def main():
    bilibili_cookie = {item.split("=")[0]: item.split("=")[1] for item in cookie.split("; ")}
    bili_jct = bilibili_cookie.get("bili_jct")
    session = requests.session()
    requests.utils.add_dict_to_cookiejar(session.cookies,bilibili_cookie)
    session.headers.update({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
        "Referer": "https://www.bilibili.com/",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
    })
    uname,is_login,coin,current_level,current_exp,next_exp = get_nav(session) # 获取当前用户信息
    List.append(f"账号昵称：{uname}")
    List.append(f"账号等级：LV{current_level}")
    List.append(f"硬币数量：{coin}")
    if is_login:
        # 抽取视频列表
        if coin_type==0: # 从指定的分区中随机抽取视频
            jsons = {"全部": 0,"动漫": 1,"游戏": 2,"电竞": 3,"鬼畜": 4,"时尚": 5,"音乐": 6,"科技": 7,"数码": 8,"知识": 9,"动物圈": 10,"美食": 11,"虚拟UP主": 12,"明星": 13,"舞蹈": 14,"生活": 15,"综艺": 16,"电影": 17,"电视剧": 18,"相声": 19,"特摄": 20,"运动": 21,"星海": 22,}
            region = random.randint(0,len(video_type)-1)
            video_list = get_region(session,regionid=jsons[region])
            pass
        elif coin_type==1: # 从指定的UP主中随机抽取一个UP主的视频
            mid = random.randint(0,len(UP_mid)-1)
            video_list = space_arc_search(session,uid=UP_mid[mid])
            print(f"抽取UP：{UP_mid[mid]}")
        vlist = random.randint(0,len(video_list)-1)
        vaid = video_list[vlist]["aid"]
        vbvid = video_list[vlist]["bvid"]
        vtitle = video_list[vlist]["title"] 
        # 开始观看视频
        report_ret = report_task(session=session,bili_jct=bili_jct,aid=vaid,bvid=vbvid)
        if report_ret["code"]==0:
            msg = f"观看视频：{vtitle}"
            vidoe_exp = 5
        else:
            msg = f"观看视频：任务失败"
            vidoe_exp = 0
        List.append(msg)
        print(msg)
        # 开始分享
        sharevideo = share_task(session,bili_jct,vaid)
        if sharevideo["code"]==0:
            List.append(f'分享成功：{vtitle}')
            share_exp=5
        elif sharevideo["code"]==71000:
            List.append(f'重复分享：{vtitle}')
            share_exp=5
        else:
            msg = f'分享任务：{vtitle}{sharevideo["message"]}'
            share_exp=0
        List.append(msg)
        print(msg)
        if coin_num > 0:
            success_coin = get_coin(session)
            for videomsg in video_list[::-1]:
                aid = videomsg["aid"]
                title = videomsg["title"]
                if success_coin >= coin_num:
                    break
                ret = coin_add(session,bili_jct,aid)
                if ret["code"]==0:
                    success_coin+=1
                    msg = f'投币成功：{title}'
                elif ret["code"]==34005:
                    msg = f'投币失败：{title}，{ret["message"]}'
                else:
                    msg = f'投币失败：{title}，{ret["message"]}，跳过投币'
                    break
                List.append(msg)
                print(msg)
            msg = f"投币任务：已投币{success_coin}个"
        else:
            msg = "投币任务：无需投币"
        List.append(msg)
        print(msg)
        # 结束
        today_exp = success_coin*10+share_exp+vidoe_exp+5
        List.append(f"今日经验：{today_exp}")
        print(f"今日经验：{today_exp}")
        update_data = round((next_exp-(current_exp+today_exp))/today_exp)
        List.append(f"升级还需：{update_data}天")
        print(f"升级还需：{update_data}天")

if __name__ == "__main__":
    if 'QYWX_Server' in os.environ:
        qywx = os.environ['QYWX_Server'].split(',')
        corpid = qywx[0]
        corpsecret = qywx[1]
        touser = qywx[2]
        agentid = qywx[3]
    if 'BiliBiliCookie' in os.environ:
        users = os.environ['BiliBiliCookie'].split('&')
        coin_num = 0
        coin_type = 0
        video_type = ["全部"]
        if "BiliBiliCoin" in os.environ:
            coin_num = int(os.environ['BiliBiliCoin'])
            if "BiliBiliType" in os.environ:
                coin_type = int(os.environ['BiliBiliType'])
                if "BiliBiliRegion" in os.environ:
                    video_type = os.environ['BiliBiliRegion'].split('&')
                if "BiliBiliUP" in os.environ:
                    UP_mid = os.environ['BiliBiliUP'].split('&')
                elif coin_type == 1:
                    print("投币模式已设置为指定UP主，但你没有填写UP主UID，将切换成分区投币")
                    coin_type = 0
        for cookie in users:
            main()
        tt = '\n'.join(List)
        # print(tt)
        if 'QYWX_Server' in os.environ:
            push('哔哩哔哩', tt)
    else:
        print('未配置Cookie')
        if 'QYWX_Server' in os.environ:
            push('BiliBili', '未配置Coookie')

