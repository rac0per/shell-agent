# 预执行校验清单

## 文档元信息
- category: safety
- intent: pre_execution_validation_checklist
- risk_level: high
- target_shell: bash,zsh

## 适用场景
- 所有涉及删除、覆盖、权限修改、服务变更的命令执行前。
- 作为高风险操作的统一闸门流程。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：pre execution validation checklist

## 同义问法
- 执行命令前要做哪些检查？
- pre execution validation checklist 标准流程。
- 如何先校验再执行？
- 高风险命令上线前检查项。
- 命令执行前需要哪些确认信息？

## 标准操作步骤
1. 语法校验：检查命令可被目标 shell 解析。
2. 风险评估：识别是否命中高风险动作与策略边界。
3. 影响预估：确认目标路径、对象数量、执行窗口。
4. 预演验证：用只读命令输出候选对象清单。
5. 审批确认：记录审批人与确认口令。

## 核心检查项
- 操作对象范围是否为绝对路径。
- 是否存在黑名单命令片段。
- 是否提供回滚步骤和回滚窗口。
- 是否存在并发任务冲突。

## 通过条件
- 语法通过。
- 风险等级符合策略，必要审批已完成。
- 预演结果与预期一致。

## 拒绝条件
- 语法错误或参数缺失。
- 命中黑名单或越权路径。
- 无回滚方案或影响范围不明确。

## 回滚方案
- 执行前保存目标对象快照或清单。
- 审批失败或确认超时立即取消任务。

## 验收标准
- 高风险命令执行前校验覆盖率达到 100%。
- 任意一次执行均可追溯到审批与预演记录。

## 关联文档
- file_operation_safety.md
- command_blacklist_policy.md
- rollback_and_recovery_playbook.md
