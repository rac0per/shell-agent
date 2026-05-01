# 目录备份任务 SOP

## 文档元信息
- category: tasks
- intent: backup_directory
- risk_level: low
- target_shell: bash,zsh

## 适用场景
- 将业务目录定期打包备份到指定路径。
- 生成带时间戳的可追溯备份文件。
- 验证备份完整性并记录备份清单。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：backup directory
- 我现在要处理 backup directory，该怎么做？

## 同义问法
- 帮我把 /data/app 做一个带日期的备份。
- 给我一个可恢复的目录打包方案。
- backup directory 的标准步骤。
- 如何定期备份目录？
- 目录打包备份怎么做？

## 任务目标
将业务目录定期打包备份到指定路径，保证可恢复性与可追溯性。

## 前置检查
- 确认源目录与目标备份目录。
- 确认目标磁盘空间充足。
- 确认备份窗口避开业务高峰。

## 操作步骤
### 第 1 步：创建带时间戳的备份文件名
TS=$(date +%Y%m%d_%H%M%S)

### 第 2 步：执行压缩备份
tar -czf /data/backup/app_${TS}.tar.gz /data/app

### 第 3 步：校验归档文件完整性
tar -tzf /data/backup/app_${TS}.tar.gz | head

### 第 4 步：记录备份清单
ls -lh /data/backup/app_${TS}.tar.gz

## 风险点
- 备份期间源目录仍变化可能导致一致性问题。
- 目标空间不足会导致备份中断。

## 回滚与应急
- 备份失败时保留错误日志并重试。
- 需要恢复时使用 tar -xzf 到恢复目录。

## 对应自然语言问法
- 帮我把 /data/app 做一个带日期的备份。
- 给我一个可恢复的目录打包方案。
