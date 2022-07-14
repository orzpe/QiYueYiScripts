#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# 账号密码用 - 分割，多个账号之间用 & 分割
# KJWJ_UP="abcd@qq.com-abcd123456&efgh@qq.com-efgh123456"

cron: 30 7 * * *
new Env('科技玩家-签到');
"""
import requests
import os,json
import time

List = []

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

def login(usr, pwd):
    session = requests.Session()
    login_url = 'https://www.kejiwanjia.com/wp-json/jwt-auth/v1/token'
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; PBEM00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.52 Mobile Safari/537.36'
    }
    data = {
        'nickname': '',
        'username': usr,
        'password': pwd,
        'code': '',
        'img_code': '',
        'invitation_code': '',
        'token': '',
        'smsToken': '',
        'luoToken': '',
        'confirmPassword': '',
        'loginType': ''
    }
    res = session.post(login_url, headers=headers, data=data)
    if res.status_code == 200:
        status = res.json()
        # print(status)
        List.append(f"账号昵称：{status.get('name')}")
        List.append(f"账号ID：{status.get('id')}")
        List.append(f"账号等级：{status.get('lv').get('lv').get('name')}")
        List.append(f"金币数量：{status.get('credit')}")
        token = status.get('token')
        get_head = {
            'authorization': f'Bearer {token}',
            'origin': 'https://www.kejiwanjia.com',
            'referer': 'https://www.kejiwanjia.com/newsflashes',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; PBEM00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.52 Mobile Safari/537.36'
        }
        respg = session.post('https://www.kejiwanjia.com/wp-json/b2/v1/getUserMission',headers=get_head)
        if respg.status_code == 200:
            check_url = 'https://www.kejiwanjia.com/wp-json/b2/v1/userMission'
            check_head = {
                'authorization': f'Bearer {token}',
                'origin': 'https://www.kejiwanjia.com',
                'referer': 'https://www.kejiwanjia.com/task',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; PBEM00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.52 Mobile Safari/537.36'

            }
            resp = session.post(check_url, headers=check_head)
            if resp.status_code == 200:
                info = resp.json()
                if type(info) == str:
                    List.append(f"已经签到过了：{info}金币")
                else:
                    List.append(f"签到成功：{info.get('credit')}金币")
    else:
        List.append('账号登录失败: 账号或密码错误')
        

if __name__ == '__main__':
    i = 0
    if 'QYWX_Server' in os.environ:
        qywx = os.environ['QYWX_Server'].split(',')
        corpid = qywx[0]
        corpsecret = qywx[1]
        touser = qywx[2]
        agentid = qywx[3]
    if 'KJWJ_UP' in os.environ:
        users = os.environ['KJWJ_UP'].split('&')
        for x in users:
            i += 1
            name, pwd = x.split('-')
            login(name, pwd)
            time.sleep(1)
        tt = '\n'.join(List)
        print(tt)
        push('科技玩家', tt)
    else:
        print('未配置环境变量')
        push('科技玩家', '未配置环境变量')
