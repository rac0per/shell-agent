# 服务健康巡检任务 SOP

## 文档元信息
- category: tasks
- intent: service_healthcheck
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：service healthcheck
- 我现在要处理 service healthcheck，该怎么做？

## 同义问法
- 帮我检查这个服务是不是健康。
- 端口和 health 接口都帮我看一下。
- service healthcheck 的标准步骤。
- 如何快速巡检服务状态？
- 服务健康检查怎么做？

## 任务目标
快速判断服务是否可用并定位常见异常点。

## 前置检查
- 确认服务名、端口、健康检查接口。
- 确认日志文件位置。

## 操作步骤
### 第 1 步：检查进程
ps -ef | grep myservice | grep -v grep

### 第 2 步：检查端口监听
ss -lntp | grep 8080

### 第 3 步：检查健康接口
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/health

### 第 4 步：检查错误日志
grep -R -n -i "error|exception" /var/log/myservice | head -50

## 风险点
- 巡检命令本身低风险，但误判可能导致错误操作。

## 回滚与应急
- 若需重启服务，先保存当前日志与状态快照。
- 结合变更记录判断异常是否由发布引起。

## 对应自然语言问法
- 帮我检查这个服务是不是健康。
- 端口和 health 接口都帮我看一下。
