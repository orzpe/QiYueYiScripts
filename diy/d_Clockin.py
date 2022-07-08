import requests,json,os,random,time

"""
建议cron: 0 16 * * *  python3 d_Clockin.py
new Env('微信小打卡程序');
环境变量
DKgroup = 圈子id，只能有一个
DKtoken = 账号token，备注为企业微信的用户id，即可推送给用户
"""

##########################分界线，下面的内容不要乱动##########################

# 设备UA
UAgent = "Mozilla/5.0 (Linux; Android 10; CMI Build/QKQ1.200830.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 XWEB/2889 MMWEBSDK/20210601 Mobile Safari/537.36 MMWEBID/6610 MicroMessenger/8.0.10.1960(0x28000A3D) Process/toolsmp WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64"
# 时间
times = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
daytime = time.strftime("%Y-%m-%d", time.localtime())

# 企业微信推送
def push(title,remark):
    content = "账号: "+remark+"\n状态: "+title+"\n来源: "+nickname+"\n"+times
    picurls = "http://oss.sharedaka.com/"+picurl+"?x-oss-process=image/resize,m_fill,w_1080,h_610/format,webp"
    urls = "http://oss.sharedaka.com/"+picurl+"?x-oss-process=image/resize,m_fill,w_1080,h_2560/format,webp"
    print(picurls)
    # 获得access_token
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + WEWORKID + '&corpsecret=' + SECRET
    re = requests.get(url).json()
    access_token = re['access_token']
    url1 = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="+ access_token
    data = {
       "touser" : remark,
       "msgtype" : "news",
       "agentid" : AGENTID,
       "news" : {
       "articles" : [{
               "title" : title,
               "description" : content,
               "picurl" : picurls,
               "url" : urls
            }]
        }
    }
    # 字符串格式
    re1 = requests.post(url=url1, data=json.dumps(data)).json()
    if re1['errcode'] == 0:
        print("推送成功")
    else:
        print("推送失败")

def search_env_name():
    # 获取token
    with open('/ql/scripts/qltoken/record.json','r',encoding='utf8') as f:
        jsons = json.load(f)
        token = jsons["data"]["token"]
    # 获取变量
    url = 'http://127.0.0.1:5700/open/envs?searchValue=DKtoken'
    headers = {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'application/json;charset=UTF-8'
    }
    rsp = json.loads(requests.get(url=url, headers=headers).text)
    return rsp["data"]

# 发送post请求
def post(url,headers,data):
    response = json.loads(requests.post(url=url, headers=headers, data=data).text)
    return response

# 验证当前token是否有效，有效则继续获取图片，无效则继续验证下一个token
def photo():
    data = {
	    "habitId": groupid,
	    "pageSize": 10,
	    "dynamicFeed": 0,
	    "pageNum": 1
    }
    headers = {
        "token": token,
        "user-agent": UAgent,
        "content-type": "application/json"
    }
    url = "https://uranus.sharedaka.com/api/v1/habit/v3/note/my/page?pageNum=1&pageSize=10&openId="+openID+"&noteCreateDate="
    jsons = json.loads(requests.get(url=url, headers=headers).text)
    # 判断登录成功与否
    if ("success" in jsons) :
        print("账号:"+remark+"\n登录成功")
        # 登陆成功，开始获取打卡创建日期
        Create = jsons['data']['pageContent'][0]['noteCreateDate'].split()[0]
        if (Create == daytime):
            print(jsons['data']['pageContent'][0]["nickName"]+"今日已打卡")
            news = jsons['data']['pageContent'][0]
        else:
            url = "https://uranus.sharedaka.com/api/v7/habit/note/get/list"
            jsons = post(url,headers,json.dumps(data))
            num = random.randint(0,4)
            if ("success" in jsons) :
                # 登陆成功，开始获取打卡创建日期
                Create = jsons['data']['pageContent'][num]['logDateStr']
                # 判断打卡创建时间是否在今天
                while Create != daytime:
                    num=num-1
                    if (num < 0):
                        print("今天还没有人打卡哦\n任务已停止\n"+times)
                        news = "noteFalse"
                        break
                    else:
                        Create = jsons['data']['pageContent'][num]['logDateStr']
                else:
                    print("今天已经有人打卡了，开始查看打卡图片数量")
                    news = jsons['data']['pageContent'][num]
            else:
                print("账号:"+remark+"\n登录失败")
                news = "loginFalse"
    else:
        print("账号:"+remark+"\n登录失败")
        news = "loginFalse"
    return news
        
# 创建打卡
def note(openid,Photopath,PhotoProperties):
    num = random.randint(1,3)
    headers = {
        "token": token,
        "user-agent": UAgent,
        "content-type": "application/x-www-form-urlencoded",
        "accept-encoding": "gzip, deflate, br"
    }
    url = 'https://uranus.sharedaka.com/api/v2/habit/note/forceCreate'
    data = "habitID="+groupid+"&openId="+openid+"&noteLat=27.8144"+str(num)+"&noteLng=114.4161"+str(num)+"&noteVisible=1&noteVideoDuration=0&noteAudioType=1&notePhoto="+Photopath+"&notePhotoProperties="+PhotoProperties+"&cloudType=tencent&notePhotoProperties=&title=&roomUserFlowId="
    jsons = post(url,headers,data)
    if ("success" in jsons) :
        news = "clockup"
        print("打卡成功")
    else:
        news = "clockdown"
        print("打卡失败")
    return news

def main():
    # 图片以及登录信息
    global picurl,nickname
    photonews = photo()
    if (photonews == "loginFalse"):
        news = "登录失败"
        # exit()
    elif (photonews == "noteFalse"):
        news = "今天还没有人打卡"
    else:
        # 图片路径
        Photopath = photonews["notePhoto"]
        if ("user" in Photopath) :
            nickname = photonews["user"]["nickName"]
        else:
            nickname = photonews["nickName"]
        q = json.loads(Photopath)
        text=""
        for i in range(len(q)):
            if (i==0):
                text="{\"notePhoto\":\""+q[i]+"\",\"width\":1080,\"height\":1920}"
            else:
                text=text+",{\"notePhoto\":\""+q[i]+"\",\"width\":1080,\"height\":1920}"
        picurl = q[0]
        PhotoProperties = "["+text+"]"
        openid = photonews["openId"]
        # 开始打卡
        notenews = note(openid,Photopath,PhotoProperties)
        if (notenews == "clockup"):
            news = "打卡成功"
        elif (notenews == "clockdown"):
            news = "打卡失败"
    return news
    
    
if __name__ == '__main__':
    # 调用变量
    if "DKtoken" in os.environ and os.environ["DKtoken"]:
        data = search_env_name()
    else:
        print("无法找到变量: DKtoken, 请检查")
        exit()
    if "DKgroup" in os.environ and os.environ["DKgroup"]:
        groupid = os.environ["DKgroup"]
    else:
        print("无法找到变量: DKgroup, 请检查")
        exit()
    if "DKopenID" in os.environ and os.environ["DKopenID"]:
        openID = os.environ["DKopenID"]
    if "WEWORK_ID" in os.environ and os.environ["WEWORK_ID"]:
        WEWORKID = os.environ["WEWORK_ID"]
    if "WEWORK_SECRET" in os.environ and os.environ["WEWORK_SECRET"]:
        SECRET = os.environ["WEWORK_SECRET"]
    if "WEWORK_AGENT_ID" in os.environ and os.environ["WEWORK_AGENT_ID"]:
        AGENTID = os.environ["WEWORK_AGENT_ID"]

    for line in range(0, len(data)):
        token = data[line]["value"]
        remark = data[line]["remarks"]
        if (data[line]["status"]==0):
            title = main()
            push(title,remark)

