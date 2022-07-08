#!/bin/bash
# 删除青龙脚本执行日志
# 日志删除频率变量，单位天，例如：export dellogday="5"
# cron: 0 22 * * *
# new Env('删除青龙日志');
delday=${dellogday}
# 执行代码
echo 即将删除${delday}天前的日志
for dir in /ql/log/*
do
    if [ -d "$dir" ];then
        for file in $dir/*
        do
            if [ -f "$file" ];then
                day=`basename $file`
                array=(${day//-/ }) 
                days=${array[0]}${array[1]}${array[2]}
                times=$((($(date +%s )-$(date +%s -d $days))/86400));
                if (( $times > $delday ));then
                    echo $file
                    rm -rf $dir/${array[0]}-${array[1]}-${array[2]}*
                fi
            fi
        done
    fi
done
echo 删除${delday}天前的日志完成