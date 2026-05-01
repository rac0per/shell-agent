# 模拟执行与二次确认规范

## 文档元信息
- category: safety
- intent: dry_run_and_confirmation
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 破坏性操作前先模拟执行，展示受影响对象。
- 批量删除、移动、权限变更前进行二次确认。
- 将高风险操作转化为可预览、可授权流程。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：dry run and confirmation
- 我现在要处理 dry run and confirmation，该怎么做？

## 同义问法
- 怎么先模拟再执行？
- dry-run 模式怎么用？
- 执行前如何预览影响范围？
- dry run and confirmation 的标准步骤。
- 如何实现二次确认机制？

## 目标
将破坏性操作转化为可预览、可确认流程，减少误删误改。

## 模拟执行原则
- 先列清单，后执行。
- 先统计数量，后确认。
- 先展示目标路径，后授权。

## 常用模拟方式
- 删除前：find ... -print
- 移动前：echo mv source target
- 批量替换前：grep 先定位命中行

## 二次确认触发条件
- 预计影响文件数超过阈值。
- 命令包含 rm、chmod、chown、mv 批量参数。
- 目标路径接近系统关键目录。

## 建议确认文案
- 将处理 N 个对象，目标路径为 XXX，是否继续。
- 检测到高风险操作，需要再次输入确认口令。

## 失败回退
- 若确认失败或超时，任务自动取消。
- 自动清理临时上下文，避免重复触发。

## 相关文档
- pre_execution_validation_checklist.md
- rollback_and_recovery_playbook.md
