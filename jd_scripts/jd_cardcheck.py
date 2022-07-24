#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# 通过监控Github仓库来查看是否有新的开卡脚本
# 如果新的开卡脚本则自动拉库并运行相关开卡任务
# 如果发现当前已有多个相关开卡任务时，将不会再运行开卡任务
# 此脚本需要安装第三方依赖：deepdiff

# 填写要监控的GitHub仓库的 用户名/仓库名/分支/脚本关键词
# 监控多个仓库请用 & 隔开
export GitRepoHost="QiYueYiya/scripts/main/opencard&QiYueYiya/jdscripts/master/opencardL"
# 运行开卡脚本前禁用开卡脚本定时任务，不填则不禁用
export opencardDisable="true"
# 通知变量，当有开卡脚本更新的时候进行通知，不填则不通知
# 参考文档：http://note.youdao.com/s/HMiudGkb，下方填写（corpid,corpsecret,touser,agentid,图片素材ID）
export QYWX_Server=""

cron: */5 0-4 * * *
new Env('开卡更新检测')
"""

from time import sleep
import requests,deepdiff,json,os

# 企业微信推送
def push(title,content):
    # 获得access_token
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + corpsecret
    re = requests.get(url).json()
    access_token = re['access_token']
    url1 = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="+ access_token
    data = {
       "touser": touser,
       "msgtype": "mpnews",
       "agentid": agentid,
       "mpnews" : {
           "articles":[{
                "title": title, 
                "thumb_media_id": mediaid,
                "content": content
            }]
        },
    }
    # 字符串格式
    re1 = requests.post(url=url1, data=json.dumps(data)).json()
    if re1['errcode'] == 0:
        print("推送成功")
    else:
        print("推送失败")

# 获取脚本ID
def qlcron(name):
    url = host+"/crons?searchValue="+name
    rsp = session.get(url=url, headers=headers)
    jsons = rsp.json()
    if rsp.status_code == 200:
        if len(jsons["data"]):
            List.append("获取任务信息成功："+jsons["data"][0]["name"])
            return jsons["data"][0]["name"],[jsons["data"][0]["_id"]]
        else:
            List.append("没有找到任务，无法获取任务信息")
            return False,False
    else:
        List.append(f'请求青龙失败：{url}')
        List.append("错误信息："+jsons["message"])
        return False,False

def qlrun(scripts_name):
    # 读取青龙登录token
    with open("/ql/config/auth.json", 'rb') as json_file:
        authjson = json.load(json_file)
    if "token" in authjson:
        token = authjson["token"]
    else:
        List.append("青龙Token获取失败")
        return
    # 向请求头添加青龙登录Token
    headers['Authorization']='Bearer '+token
    url = host+"/crons/run"
    # 获取仓库任务信息
    RepoName,RepoID = qlcron(GitRepo)
    if not RepoName:
        List.append(f"获取仓库任务信息失败：{GitRepo}")
        return
    # 运行拉取仓库任务
    File = os.path.exists("/ql/scripts/"+GitRepoHost[0]+"_"+GitRepoHost[1]+"/"+scripts_name)
    while not File:
        List.append(f"没有找到{scripts_name}文件，即将更新仓库")
        rsp = session.put(url=url,headers=headers,data=json.dumps(RepoID))
        if rsp.status_code == 200:
            List.append(f"运行拉库任务：{RepoName}")
        else:
            List.append(f'请求青龙失败：{url}')
            List.append("错误信息："+rsp.json()["message"])
            return
        sleep(10)
        File = os.path.exists("/ql/scripts/"+GitRepoHost[0]+"_"+GitRepoHost[1]+"/"+scripts_name)
    else:
        List.append(f"已找到{scripts_name}文件，即将获取相关任务信息")
    # 获取开卡任务信息
    TaskName,TaskID = qlcron(scripts_name)
    if not TaskName:
        List.append(f"获取开卡任务信息失败：{scripts_name}")
        return
    # 禁用开卡任务
    if 'opencardDisable' in os.environ:
        Disable = os.environ['opencardDisable']
        if Disable=="true":
            vurl = host+"/crons/disable"
            rsp = session.put(url=vurl,headers=headers,data=json.dumps(TaskID))
            if rsp.status_code == 200:
                List.append(f"禁用开卡任务：{TaskName}")
            else:
                List.append(f'请求青龙失败：{url}')
                List.append("错误信息："+rsp.json()["message"])
                return
    # 查找当前是否有多个同名开卡任务
    namename = TaskName.split(" ")
    if len(namename)>1:
        namename = namename[1]
    else:
        namename = namename[0]
    vurl = host+"/crons?searchValue="+namename
    rsp = session.get(url=vurl, headers=headers).json()
    if len(rsp["data"])>1:
        List.append(f"找到多个任务：{TaskName}")
        # 查看当前任务是否运行过
        for a in rsp["data"]:
            xurl = host+"/crons/"+a["_id"]
            xrsp = session.get(url=xurl, headers=headers).json()
            if "last_execution_time" in xrsp["data"]:
                List.append("该任务曾运行："+xrsp["data"]["name"]+"\n放弃运行任务"+TaskName)
                break
            else:
                List.append("从未运行任务："+xrsp["data"]["name"])
    # 运行开卡任务
    rsp = session.put(url=url,headers=headers,data=json.dumps(TaskID))
    if rsp.status_code == 200:
        List.append(f"运行开卡任务：{TaskName}")
    else:
        List.append(f'请求青龙失败：{url}')
        List.append("错误信息："+rsp.json()["message"])
        
def main():
    state = True
    # 请求Github仓库获取目录树
    rsp = session.get(url=api,headers=headers)
    if rsp.status_code != 200:
        List.append(f'请求GitHub失败：{api}')
        return state
    # 只保存目录树中的开卡脚本的文件名信息
    tree = []
    for x in rsp.json()["tree"]:
        if GitRepoHost[3] in x["path"]:
            tree.append(x["path"])
    # 查看是否有tree.json文件
    if not os.path.exists(f"/ql/scripts/{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json"):
        with open(f"/ql/scripts/{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json","w") as f:
            json.dump(tree,f)
        List.append(f"没有找到{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json文件！将自动生成")
    # 读取上一次保存的tree.json并与当前tree进行对比
    with open(f"/ql/scripts/{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json", 'rb') as json_file:
        tree_json = json.load(json_file)
    diff = deepdiff.DeepDiff(tree_json, tree)
    # 判断是否有新增开卡脚本
    if "values_changed" in diff:
        for x in diff["values_changed"]:
            scripts_name = diff["values_changed"][x]["new_value"]
            List.append(f"新增开卡脚本：{scripts_name}")
            # 拉库运行开卡脚本
            qlrun(scripts_name)
            break
    elif "iterable_item_added" in diff:
        for x in diff["iterable_item_added"]:
            scripts_name = diff["iterable_item_added"][x]
            List.append(f"新增开卡脚本：{scripts_name}")
            # 拉库运行开卡脚本
            qlrun(scripts_name)
            break
    else:
        List.append("没有新增开卡脚本")
        state=False
    with open(f"/ql/scripts/{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json","w") as f:
        List.append(f"保存数据到{GitRepoHost[0]}_{GitRepoHost[1]}/tree.json文件")
        json.dump(tree,f)
    return state

if 'QYWX_Server' in os.environ:
    qywx = os.environ['QYWX_Server'].split(',')
    corpid = qywx[0]
    corpsecret = qywx[1]
    touser = qywx[2]
    agentid = qywx[3]
    mediaid = qywx[4]
if 'GitRepoHost' in os.environ:
    session = requests.session()
    host = 'http://127.0.0.1:5700/api'
    RepoHost = os.environ['GitRepoHost'].split("&")
    for RepoX in RepoHost:
        List = []
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        GitRepoHost = RepoX.split("/")
        GitRepo = GitRepoHost[0]+"/"+GitRepoHost[1]
        GitBranch = GitRepoHost[2]
        List.append(f"监控仓库：https://github.com/{GitRepo}")
        api = f'https://api.github.com/repos/{GitRepo}/git/trees/{GitBranch}'
        state = main()
        tt = '\n'.join(List)
        print(tt)
        if (state) and ('QYWX_Server' in os.environ):
            push('开卡更新检测', tt)
else:
    print("请查看脚本注释后设置相关变量")
 
