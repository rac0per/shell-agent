# crontab 定时任务命令卡

## 文档元信息
- category: commands
- intent: cron_basic_tasks
- risk_level: low
- target_shell: bash,zsh

## 适用场景
- 配置周期性任务，例如备份和日志清理。
- 设置定时脚本定期执行。
- 查看和管理当前系统的 cron 任务列表。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：cron basic tasks
- 我现在要处理 cron basic tasks，该怎么做？

## 同义问法
- 每天凌晨 3 点执行脚本怎么配置？
- 查看当前定时任务。
- 如何设置 crontab 定时任务？
- cron job 怎么写？
- 定时任务怎么添加和查看？
- cron basic tasks 的标准步骤。

## 标准操作步骤
1. 查看当前用户的 crontab：`crontab -l`
2. 编辑 crontab：`crontab -e`
3. 按 cron 语法写入规则：`分 时 日 月 周 命令`
4. 保存退出后 cron 自动生效。
5. 验证写入：再次执行 `crontab -l` 确认规则存在。

## 推荐命令
crontab -l
crontab -e

## 示例规则
0 3 * * * /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1
30 2 * * 0 /usr/local/bin/backup.sh

## 参数说明
- `crontab -l`：列出当前用户的定时任务。
- `crontab -e`：编辑定时任务，保存后立即生效。
- `crontab -r`：删除当前用户全部定时任务（慎用）。
- cron 表达式五字段：分钟、小时、日、月、星期。

## 风险与边界
- 写入计划任务配置，需确认脚本路径和权限。
- 脚本必须有可执行权限且路径为绝对路径。
- 不要用 `crontab -r` 替代 `crontab -e`，前者会清空全部规则。

## 回滚方案
- 若误删 crontab，尽快从备份恢复：`crontab /tmp/crontab_backup`
- 修改前建议先备份：`crontab -l > /tmp/crontab_backup`

## 验收标准
- `crontab -l` 显示新增规则。
- 等到下次触发时间，确认日志有执行记录。

## 关联文档
- ../tasks/scheduled_task_rotation_sop.md
- ../tasks/temp_file_cleanup_sop.md
