# 批量权限修复 SOP

## 文档元信息
- category: tasks
- intent: batch_permission_fix
- risk_level: high
- target_shell: bash,zsh

## 任务目标
- 修复目录权限异常，保障服务可访问且不过度授权。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：batch permission fix

## 同义问法
- 批量修权限但别影响服务。
- batch permission fix 的 SOP。
- 目录文件权限统一修复流程。
- 修复 chmod/chown 异常步骤。
- 权限改完如何验证服务可用？

## 标准操作步骤
1. 导出权限快照：保留变更前证据。
2. 小范围试修：先选 1 个子目录验证。
3. 全量修复目录权限（755）。
4. 全量修复文件权限（644）。
5. 修复属主并验证服务可用。

## 推荐命令
find /data/app -maxdepth 2 -exec ls -ld {} \; > /tmp/app_perm_before.txt
find /data/app -type d -exec chmod 755 {} \;
find /data/app -type f -exec chmod 644 {} \;
chown -R appuser:appgroup /data/app
systemctl status app.service

## 风险与边界
- 禁止对系统目录（如 `/`、`/etc`）递归 chmod/chown。
- 错误属主会导致服务启动失败。

## 回滚方案
- 根据快照回放关键目录权限。
- 若服务异常，优先恢复应用配置目录权限与属主。

## 验收标准
- 服务启动与访问正常。
- 核心目录权限符合最小权限原则。

## 关联文档
- ../commands/change_permissions_chmod.md
- ../commands/change_owner_chown.md
- ../safety/pre_execution_validation_checklist.md
