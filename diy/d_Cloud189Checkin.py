import requests,time,re,rsa,json,base64,os

"""
说明: 环境变量`Cloud189`，账号密码用`-`分割，多个账号用`&`分割
例如：Cloud189="189****1234-666666&188****5678-888888"
cron: 30 7 * * *
new Env('天翼云盘-签到');
"""

def main():
    rand = str(round(time.time()*1000))
    surl = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K'
    url = 'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
    url2 = 'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN'
    headers = {
        'User-Agent':'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
        "Referer" : "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host" : "m.cloud.189.cn",
        "Accept-Encoding" : "gzip, deflate",
    }
    #签到
    response = s.get(surl,headers=headers)
    netdiskBonus = response.json()['netdiskBonus']
    List.append(f"签到结果：获得{netdiskBonus}MB空间")
    response = s.get(url=url, headers=headers)
    if "errorCode" in response.text:
        if response.json().get("errorCode") == "User_Not_Chance":
            description = "没有抽奖机会了"
        else:
            description = response.json().get("errorCode")
        List.append(f"第一次抽：{description}")
    else:
        description = response.json().get("description", "")
        if description in ["1", 1]:
            description = "50MB空间"
        List.append(f"第一次抽：获得{description}")
    response = s.get(url=url2, headers=headers)
    if "errorCode" in response.text:
        if response.json().get("errorCode") == "User_Not_Chance":
            description = "没有抽奖机会了"
        else:
            description = response.json().get("errorCode")
        List.append(f"第二次抽：{description}")
    else:
        description = response.json().get("description", "")
        if description in ["1", 1]:
            description = "50MB空间"
        List.append(f"第二次抽：获得{description}")

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")

def int2char(a):
    return BI_RM[a]

b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = b64map.index(list(a)[i])
            if 0 == e:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif 1 == e:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif 2 == e:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d

def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result

def login(s,username, password):
    url = "https://cloud.189.cn/api/portal/loginUrl.action?redirectURL=https://cloud.189.cn/web/redirect.html"
    r = s.get(url)
    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl = '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
    s.headers.update({"lt": lt})
    username = rsa_encode(j_rsakey, username)
    password = rsa_encode(j_rsakey, password)
    url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
        'Referer': 'https://open.e.189.cn/',
        }
    data = {
        "appKey": "cloud",
        "accountType": '01',
        "userName": f"{{RSA}}{username}",
        "password": f"{{RSA}}{password}",
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
        }
    r = s.post(url, data=data, headers=headers, timeout=5)
    if r.json()["result"] == 0:
        redirect_url = r.json()["toUrl"]
        s.get(url=redirect_url)
        return True
    else:
        return r.json()["msg"]

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

if __name__ == "__main__":
    List = []
    if 'QYWX_Server' in os.environ:
        qywx = os.environ['QYWX_Server'].split(',')
        corpid = qywx[0]
        corpsecret = qywx[1]
        touser = qywx[2]
        agentid = qywx[3]
    if 'Cloud189' in os.environ:
        users = os.environ['Cloud189'].split('&')
        for x in users:
            s = requests.Session()
            username,password = x.split('-')
            msgs = login(s,username,password)
            List.append(f"账号信息：{username[:3]}****{username[7:]}")
            if (msgs == True):
                main()
            else:
                List.append(f"登录信息：{msgs}")
            time.sleep(1)
        tt = '\n'.join(List)
        print(tt)
        push('天翼云盘',tt)
    else:
        print('未配置账号')
        push('天翼云盘','未配置账号')
