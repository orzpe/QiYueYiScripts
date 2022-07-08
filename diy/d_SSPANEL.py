# -*- coding: utf-8 -*-
import requests,os,json

"""
环境变量：SSPANEL
变量格式：域名-账号-密码，多个站点使用 ; 隔开
例如 SSPANEL="https://abc.com-abc@qq.com-abc123456;https://abc.com-abc@qq.com-abc123456;"
cron: 30 7 * * *
new Env('SSPANEL-签到');
"""

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

def sign(email, password, url):
    email = email.replace("@", "%40")
    try:
        requests.packages.urllib3.disable_warnings()
        session = requests.session()
        session.get(url=url, verify=False)
        login_url = url + "/auth/login"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        post_data = "email=" + email + "&passwd=" + password + "&code="
        post_data = post_data.encode()
        session.post(login_url, post_data, headers=headers, verify=False)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "Referer": url + "/user",
        }
        response = session.post(url + "/user/checkin", headers=headers, verify=False)
        List.append("签到信息："+response.json().get("msg"))
    except Exception as e:
        List.append("签到信息: 签到失败")


if __name__ == "__main__":
    List = []
    if 'QYWX_Server' in os.environ:
        qywx = os.environ['QYWX_Server'].split(',')
        corpid = qywx[0]
        corpsecret = qywx[1]
        touser = qywx[2]
        agentid = qywx[3]
    if 'SSPANEL' in os.environ:
        users = os.environ['SSPANEL'].split(';')
        for x in users:
            url,email,password = x.split('-')
            List.append(f"站点信息：{url}")
            List.append(f"帐号信息：{email}")
            sign_msg = sign(email=email, password=password, url=url)
        tt = '\n'.join(List)
        print(tt)
        push('SSPANEL', tt)
    else:
        print('未配置环境变量')
        push('SSPANEL', '未配置环境变量')

