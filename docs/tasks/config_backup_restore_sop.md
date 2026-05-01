# 配置文件备份与恢复 SOP

## 文档元信息
- category: tasks
- intent: config_backup_restore
- risk_level: medium
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：config backup restore
- 我现在要处理 config backup restore，该怎么做？

## 同义问法
- 改配置前先备份，失败可回滚。
- 给我一个配置变更的安全流程。
- config backup restore 的标准步骤。
- 配置文件如何备份和恢复？
- 修改配置前后怎么保证可回滚？

## 任务目标
在修改配置前后保证可快速回滚，降低变更风险。

## 前置检查
- 确认配置文件路径。
- 确认备份目录权限。
- 确认服务重载方式。

## 操作步骤
### 第 1 步：备份原配置
TS=$(date +%Y%m%d_%H%M%S) && cp -a /etc/myapp/config.yaml /data/backup/config.yaml.${TS}

### 第 2 步：执行配置变更
sed -i.bak 's/old_value/new_value/g' /etc/myapp/config.yaml

### 第 3 步：语法或关键项校验
grep -n "new_value" /etc/myapp/config.yaml

### 第 4 步：恢复（如变更失败）
cp -a /data/backup/config.yaml.${TS} /etc/myapp/config.yaml

## 风险点
- 直接改生产配置可能导致服务不可用。

## 回滚与应急
- 始终保留时间戳备份。
- 回滚后执行服务健康检查。

## 对应自然语言问法
- 改配置前先备份，失败可回滚。
- 给我一个配置变更的安全流程。
