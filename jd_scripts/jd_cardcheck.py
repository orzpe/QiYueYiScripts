#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# 通过监控Github仓库来查看是否有新的开卡脚本
# 如果有则自动拉库并运行开卡脚本
# 此脚本需要安装第三方依赖：deepdiff
# 填写要监控的GitHub仓库的用户名和仓库名
export GitRepoHost="QiYueYiya/scripts"

## 参考文档：http://note.youdao.com/s/HMiudGkb
## 下方填写（corpid,corpsecret,touser,agentid）
export QYWX_AM=""

cron: */5 0-6 * * *
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

# 获取脚本ID
def qlcron(name):
    url = host+"/crons?searchValue="+name
    rsp = session.get(url=url, headers=headers)
    jsons = json.loads(rsp.text)
    if rsp.status_code == 200:
        List.append("获取任务ID成功："+jsons["data"][0]["name"])
        return jsons["data"][0]["name"],[jsons["data"][0]["_id"]]
    else:
        List.append(f'请求失败：{url}')
        List.append("错误信息："+json.loads(rsp.text)["message"])
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
    url = host+"/crons/run"
    # 向请求头添加青龙登录Token
    headers['Authorization']='Bearer '+token
    # 获取仓库任务ID
    RepoName,RepoID = qlcron(GitRepo)
    if not RepoName:
        List.append(f"获取任务ID失败：{GitRepo}")
        return
    # 运行拉取仓库任务
    GitPath = GitRepo.split("/")
    File = os.path.exists("/ql/scripts/"+GitPath[0]+"_"+GitPath[1]+"/"+scripts_name)
    while not File:
        List.append(f"没有找到{scripts_name}文件，即将更新仓库")
        rsp = session.put(url=url,headers=headers,data=json.dumps(RepoID))
        if rsp.status_code == 200:
            List.append(f"运行任务：{RepoName}")
        else:
            List.append(f'请求失败：{url}')
            List.append("错误信息："+json.loads(rsp.text)["message"])
            return
        sleep(10)
        File = os.path.exists("/ql/scripts/"+GitPath[0]+"_"+GitPath[1]+"/"+scripts_name)
    # 获取开卡任务ID
    TaskName,TaskID = qlcron(scripts_name)
    if not TaskName:
        List.append(f"获取任务ID失败：{scripts_name}")
        return
    # 运行开卡任务
    rsp = session.put(url=url,headers=headers,data=json.dumps(TaskID))
    if rsp.status_code == 200:
        List.append(f"运行任务：{TaskName}")
    else:
        List.append(f'请求失败：{url}')
        List.append("错误信息："+json.loads(rsp.text)["message"])
        return

def main():
    # 请求Github仓库获取目录树
    rsp = session.get(url=api,headers=headers)
    if rsp.status_code != 200:
        List.append(f'请求失败：{api}')
        return
    # 只保存目录树中的开卡脚本的文件名信息
    tree = []
    for x in json.loads(rsp.text)["tree"]:
        if "opencard" in x["path"]:
            tree.append(x["path"])
    # 查看是否有tree.json文件
    if not os.path.exists("./tree.json"):
        with open("./tree.json","w") as f:
            json.dump(tree,f)
        List.append("没有找到tree.json文件！即将保存数据为tree.json文件")
    # 读取上一次保存的tree.json并与当前tree进行对比
    with open("./tree.json", 'rb') as json_file:
        tree_json = json.load(json_file)
    diff = deepdiff.DeepDiff(tree_json, tree)
    state=True
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
    with open("./tree.json","w") as f:
        List.append("保存数据到tree.json文件")
        json.dump(tree,f)
    tt = '\n'.join(List)
    print(tt)
    if state and qywx:
        push('监控开卡', tt)

if 'QYWX_Server' in os.environ:
    qywx = os.environ['QYWX_Server'].split(',')
    corpid = qywx[0]
    corpsecret = qywx[1]
    touser = qywx[2]
    agentid = qywx[3]
else:
    qywx = False
    print("未填写通知变量QYWX_Server，将不进行推送")
if 'GitRepoHost' in os.environ:
    List = []
    GitRepo = os.environ['GitRepoHost']
    List.append(f"监控仓库：https://github.com/{GitRepo}")
    api = f'https://api.github.com/repos/{GitRepo}/git/trees/main'
    host = 'http://127.0.0.1:5700/api'
    headers = {
        'accept': 'application/json',
        "Content-Type": "application/json;charset=UTF-8"
    }
    session = requests.session()
    main()
else:
    print("请查看脚本注释后设置相关变量")
 
