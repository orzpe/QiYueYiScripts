#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# 目前仅支持单个脚本更新的情况下，如果该仓库一次更新多个脚本，则此脚本有可能出错
# 需要安装第三方依赖：deepdiff

# 要监控的GitHub仓库，例如监控的仓库为：https://github.com/opencard/scripts
# 则填写链接中的用户名和仓库名，如下
export GitRepoHost="opencard/scripts"

cron: */5 0-6 * * *
new Env('开卡更新检测')
"""

from notify import send
from time import sleep
import requests,json,deepdiff,os

# 获取脚本ID
def qlcron(name):
    url = host+"/crons?searchValue="+name
    rsp = session.get(url=url, headers=headers)
    jsons = json.loads(rsp.text)
    if rsp.status_code == 200:
        print("获取任务ID成功："+jsons["data"][0]["name"])
        return jsons["data"][0]["name"],[jsons["data"][0]["_id"]]
    else:
        print(f'请求失败：{url}')
        return False,False

def qlrun(scripts_name):
    url = host+"/crons/run"
    GitPath = GitRepo.split("/")
    RepoName,RepoID = qlcron(GitRepo)
    if not RepoName:
        print(f"获取任务ID失败：{GitRepo}")
        return
    # 运行拉取仓库任务
    File = os.path.exists("/ql/scripts/"+GitPath[0]+"_"+GitPath[1]+"/"+scripts_name)
    while not File:
        rsp = session.put(url=url,headers=headers,data=json.dumps(RepoID))
        if rsp.status_code == 200:
            print(f"运行任务：{RepoName}")
        else:
            print(f'请求失败：{url}')
        sleep(5000)
        File = os.path.exists("/ql/scripts/"+GitPath[0]+"_"+GitPath[1]+"/"+scripts_name)
    # 运行开卡任务
    TaskName,TaskID = qlcron(scripts_name)
    if not TaskName:
        print(f"获取任务ID失败：{scripts_name}")
        return
    rsp = session.put(url=url,headers=headers,data=json.dumps(TaskID))
    if rsp.status_code == 200:
        print(f"运行任务：{TaskName}")
    else:
        print(f'请求失败：{url}')
        return

def main():
    # 请求Github获取目录树
    rsp = session.get(url=api,headers=headers)
    if rsp.status_code != 200:
        print(f'请求失败：{api}')
        return
    # 只保存目录中的文件名信息
    tree = []
    for x in json.loads(rsp.text)["tree"]:
        tree.append(x["path"])
    # 查看是否有目录树json
    if not os.path.exists("./tree.json"):
        with open("./tree.json","w") as f:
            json.dump(tree,f)
        print("当前没有已保存的目录树，将保存当前目录树")
    # 读取上一次保存的目录树并与当前目录树进行对比
    with open("./tree.json", 'rb') as json_file:
        tree_json = json.load(json_file)
    diff = deepdiff.DeepDiff(tree_json, tree)
    # 判断是否有新增文件
    if "values_changed" in diff:
        for x in diff["values_changed"]:
            scripts_name = diff["values_changed"][x]["new_value"]
            # 如果新增文件名包含opencard
            if "opencard" in scripts_name:
                print(f"新增开卡：{scripts_name}")
                # 拉库运行开卡脚本
                headers['Authorization']='Bearer '+token
                content = qlrun(scripts_name)
                send("开卡更新检测",content)
            else:
                print("仓库有更新，但没有新增开卡脚本")
            break
    else:
        print("没有新增开卡脚本")
    # 保存当前目录树
    with open("./tree.json","w") as f:
        json.dump(tree,f)
        print("保存当前目录树")

if 'GitRepoHost' in os.environ:
    GitRepo = os.environ['GitRepoHost']
    api = f'https://api.github.com/repos/{GitRepo}/git/trees/main'
    host = 'http://127.0.0.1:5700/api'
    # 读取青龙登录token
    with open("/ql/config/auth.json", 'rb') as json_file:
        token = json.load(json_file)["token"]
    headers = {
        'accept': 'application/json',
        "Content-Type": "application/json;charset=UTF-8"
    }
    session = requests.session()
    main()
else:
    print("请查看脚本注释后设置相关变量")
 
