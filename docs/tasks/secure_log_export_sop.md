# 安全日志导出 SOP

## 文档元信息
- category: tasks
- intent: secure_log_export
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 将日志按时间范围导出并脱敏处理。
- 供审计或排障使用的安全日志打包导出。
- 生成带校验值的脱敏日志压缩包。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：secure log export
- 我现在要处理 secure log export，该怎么做？

## 同义问法
- 帮我导出今天日志并做脱敏打包。
- 如何安全导出日志供审计？
- secure log export 的标准步骤。
- 日志脱敏导出怎么做？
- 安全日志导出 SOP 是什么？

## 任务目标
将日志按范围导出并脱敏，供审计或排障使用。

## 前置检查
- 确认导出时间范围和日志类型。
- 确认导出目录访问权限。
- 确认是否包含敏感字段。

## 操作步骤
### 第 1 步：筛选时间范围（示例）
grep "2026-03-10" /var/log/app/app.log > /tmp/app_20260310.log

### 第 2 步：脱敏处理（示例）
sed -E 's/[0-9]{11}/<PHONE>/g; s/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+/<EMAIL>/g' /tmp/app_20260310.log > /tmp/app_20260310_masked.log

### 第 3 步：压缩导出
tar -czf /data/export/app_20260310_masked.tar.gz /tmp/app_20260310_masked.log

### 第 4 步：生成校验值
sha256sum /data/export/app_20260310_masked.tar.gz

## 风险点
- 脱敏规则不完整会导致敏感信息泄露。

## 回滚与应急
- 导出失败时删除中间文件并重新执行。
- 导出完成后清理临时明文日志。

## 对应自然语言问法
- 帮我导出今天日志并做脱敏打包。
