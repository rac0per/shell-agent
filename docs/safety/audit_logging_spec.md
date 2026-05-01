# 安全审计日志规范

## 文档元信息
- category: safety
- intent: audit_logging_spec
- risk_level: high
- target_shell: bash,zsh

## 适用场景
- 对命令生成与执行流程进行审计留痕。
- 发生误删、越权、故障时快速追溯责任与链路。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：audit logging spec

## 同义问法
- 审计日志需要记录哪些字段？
- audit logging spec 的标准规范。
- 命令执行怎么做可追溯记录？
- 安全日志怎么分级？
- 风险命令的审计字段有哪些？

## 标准操作步骤
1. 定义审计事件模型（生成、确认、执行、回滚）。
2. 落地必填字段与字段校验规则。
3. 按风险级别写入不同日志通道。
4. 建立检索索引与告警规则。
5. 每周抽样校验日志完整性与可追溯性。

## 必填字段
- trace_id
- session_id
- user_id
- natural_language_input
- generated_command
- risk_level
- execution_status
- started_at
- finished_at

## 推荐扩展字段
- target_shell
- target_paths
- affected_count
- simulated_preview
- approval_id
- rollback_command
- error_message

## 风险与边界
- 缺失关键字段会导致审计不可用。
- 日志包含敏感数据时必须脱敏。
- 禁止直接覆盖历史日志，需仅追加写入。

## 回滚方案
- 日志管道异常时切换到本地 fallback 队列。
- 修复后批量补写，并记录补写范围。

## 验收标准
- 高风险操作日志字段完整率达到 100%。
- 任意一次命令可在 2 分钟内完成链路追溯。

## 关联文档
- permission_control_policy.md
- command_blacklist_policy.md
- rollback_and_recovery_playbook.md
