# 自动检测github项目是否更新

import time
import requests

name = 'feverrun/my_scripts'

api = 'https://api.github.com/repos/' + name
weburl = 'https://github.com' + name

old_time = None
# 一直监听
while True:
    # get方法请求链接
    r = requests.get(api)
    # 返回200请求成功，不是200请求失败
    if r.status_code != 200:
        print('请求api失败')
        break
    # json --> dict
    now_time = r.json()['pushed_at']

    if not old_time:
        old_time = now_time
    if old_time < now_time:
        print('项目更新了')
    print(f'检测中{now_time}')
    # 60 * 10   -->  10分钟
    time.sleep(60)