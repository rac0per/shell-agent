# 磁盘容量应急处理 SOP

## 文档元信息
- category: tasks
- intent: disk_capacity_emergency
- risk_level: high
- target_shell: bash,zsh

## 任务目标
- 当磁盘逼近告警阈值时，快速定位占用热点并低风险缓解。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：disk capacity emergency

## 同义问法
- 磁盘快满了怎么应急处理？
- disk capacity emergency SOP。
- 先查哪里占空间，再安全处理。
- 磁盘 90% 以上处理步骤。
- 不删关键日志的清理方案。

## 标准操作步骤
1. 确认告警挂载点与当前使用率。
2. 定位占用最大目录与大文件。
3. 预演可回收对象清单。
4. 优先执行压缩/迁移，最后再删除。
5. 复核容量变化并记录复盘信息。

## 推荐命令
df -h
du -sh /* 2>/dev/null | sort -hr | head -20
find /var -type f -size +500M 2>/dev/null
find /var/log -type f -name "*.log" -mtime +7 -print
find /var/log -type f -name "*.log" -mtime +7 -print0 | xargs -0 gzip

## 风险与边界
- 禁止直接删除审计与交易日志。
- 高峰期批量压缩可能导致 I/O 抖动，建议限流或错峰。

## 回滚方案
- 压缩前先导出清单。
- 若业务依赖旧日志，解压恢复：`gunzip <file>.gz`。

## 验收标准
- 挂载点使用率回到安全阈值以下。
- 关键服务响应正常，无日志缺失告警。

## 关联文档
- ../commands/disk_usage_du_df.md
- ../commands/find_large_files.md
- ../safety/file_operation_safety.md
