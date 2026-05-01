# 定时任务轮转维护 SOP

## 文档元信息
- category: tasks
- intent: scheduled_task_rotation
- risk_level: medium
- target_shell: bash,zsh

## 任务目标
- 保证 cron 任务稳定运行，并定期清理重复、冲突和失效任务。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：scheduled task rotation

## 同义问法
- scheduled task rotation 的标准步骤。
- 安全新增一个每天凌晨任务。
- cron 任务轮转维护怎么做？
- 如何避免 crontab 被覆盖？
- 定时任务冲突检查流程。

## 标准操作步骤
1. 导出现有任务备份。
2. 识别重复任务与冲突时间窗。
3. 追加新任务而非覆盖原任务。
4. 验证任务已生效并检查日志路径。
5. 设定失败告警与每周巡检。

## 推荐命令
crontab -l > /tmp/cron_backup_$(date +%Y%m%d_%H%M%S).txt
crontab -l | sort | uniq -d
( crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1" ) | crontab -
crontab -l

## 风险与边界
- 直接 `crontab file` 覆盖风险高，需先备份。
- 输出日志路径不可写会导致静默失败。

## 回滚方案
- 回滚命令：`crontab /tmp/cron_backup_xxx.txt`。
- 回滚后验证关键任务仍在计划中。

## 验收标准
- 任务条目正确，无重复与冲突。
- 最近一次任务执行日志可追踪。

## 关联文档
- ../commands/cron_basic_tasks.md
- ../safety/audit_logging_spec.md
