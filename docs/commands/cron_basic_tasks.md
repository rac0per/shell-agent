# crontab 定时任务命令卡

## 适用场景
- 配置周期性任务，例如备份和日志清理。

## 用户常见问法
- 每天凌晨 3 点执行脚本。
- 查看当前定时任务。

## 推荐命令
crontab -l
crontab -e

## 示例规则
0 3 * * * /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1

## 风险与回滚
- 写入计划任务配置，需确认脚本路径和权限。
