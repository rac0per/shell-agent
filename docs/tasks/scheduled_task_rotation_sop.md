# 定时任务轮转维护 SOP

## 任务目标
保证 cron 任务稳定运行，并定期审计失效或重复任务。

## 前置检查
- 确认任务执行账号。
- 确认日志输出路径。
- 确认任务脚本可执行权限。

## 操作步骤
### 第 1 步：导出现有任务
crontab -l > /tmp/cron_backup_$(date +%Y%m%d_%H%M%S).txt

### 第 2 步：检查重复和冲突
crontab -l | sort | uniq -d

### 第 3 步：追加新任务（示例）
( crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1" ) | crontab -

### 第 4 步：验证任务生效
crontab -l

## 风险点
- 直接覆盖 crontab 容易丢失历史任务。

## 回滚与应急
- 使用导出备份快速恢复旧任务。
- 对关键任务增加失败告警。

## 对应自然语言问法
- 帮我安全地新增一个每天凌晨执行的任务。
