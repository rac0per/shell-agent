# 安全审计日志规范

## 目标
实现可追溯、可审计、可复盘的命令执行日志。

## 必填字段
- trace_id
- session_id
- user_id
- role
- natural_language_input
- generated_command
- risk_level
- approval_id
- execution_status
- started_at
- finished_at

## 推荐扩展字段
- target_shell
- target_paths
- affected_count
- simulated_preview
- rollback_command
- error_message

## 日志分级
- INFO: 查询类命令。
- WARN: 中风险写操作。
- ERROR: 拒绝执行或执行失败。
- SECURITY: 命中黑名单或疑似攻击。

## 存储建议
- 结构化 JSON 行日志，便于检索。
- 定期归档到只读存储。
- 关键日志设置防篡改策略。

## 检索建议
- 按 session_id 查询会话级行为。
- 按 user_id 查询用户历史操作。
- 按 risk_level 和 execution_status 做风控报表。

## 相关文档
- permission_control_policy.md
- command_blacklist_policy.md
