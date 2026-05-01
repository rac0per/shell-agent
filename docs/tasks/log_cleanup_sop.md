# 日志清理任务 SOP

## 文档元信息
- category: tasks
- intent: log_cleanup
- risk_level: low
- target_shell: bash,zsh

## 适用场景
- 压缩并清理历史日志，控制磁盘占用。
- 保留可追溯性，同时清理过期日志。
- 配置日志保留策略（如保留 7 天）。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：log cleanup
- 我现在要处理 log cleanup，该怎么做？

## 同义问法
- 帮我清理老日志但保留最近一周。
- 把 7 天前日志压缩一下，别直接删。
- 统计一下哪些日志最占空间再决定是否清理。
- log cleanup 的标准步骤。
- 日志清理 SOP 是什么？

## 任务目标
压缩并清理历史日志，控制磁盘占用，同时保留可追溯性。

## 前置检查
- 确认日志目录：/var/log 或业务日志目录。
- 确认保留策略：例如保留最近 7 天。
- 确认磁盘余量与归档路径可写。

## 操作步骤
### 第 1 步：查询候选日志
find /var/log -type f -name "*.log" -mtime +7

### 第 2 步：预览将被处理的文件
find /var/log -type f -name "*.log" -mtime +7 -print

### 第 3 步：执行压缩
find /var/log -type f -name "*.log" -mtime +7 -print0 | xargs -0 gzip

### 第 4 步：验证结果
find /var/log -type f -name "*.gz" -mtime -1

## 可选删除策略
- 若压缩后需删除超长期归档，可按 90 天策略清理。
- 示例：find /var/log -type f -name "*.gz" -mtime +90 -delete

## 风险点
- 应用可能仍在写入日志，需避开业务高峰。
- 删除策略过激会影响审计与问题排查。

## 回滚与应急
- 压缩操作可通过 gunzip 恢复。
- 删除操作建议先移动到隔离目录再延迟清理。

## 对应自然语言问法
- 帮我清理老日志但保留最近一周。
- 把 7 天前日志压缩一下，别直接删。
- 统计一下哪些日志最占空间再决定是否清理。
