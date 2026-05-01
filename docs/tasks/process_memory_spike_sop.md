# 进程内存飙升排查 SOP

## 文档元信息
- category: tasks
- intent: process_memory_spike
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 内存异常飙升时快速定位高占用进程。
- 保留内存排查证据供后续复盘。
- OOM 告警响应流程。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：process memory spike
- 我现在要处理 process memory spike，该怎么做？

## 同义问法
- 内存突然飙高，帮我快速定位问题进程。
- 如何排查进程内存占用过高？
- process memory spike 的标准步骤。
- 哪个进程在吃内存，怎么查？
- 内存飙升 SOP 是什么？

## 任务目标
在内存异常上涨时快速定位高占用进程并保留排查证据。

## 前置检查
- 确认告警时间窗口。
- 确认目标主机与服务名。
- 确认是否允许采样诊断命令。

## 操作步骤
### 第 1 步：查看整体内存
free -h

### 第 2 步：按内存排序查看进程
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -30

### 第 3 步：跟踪可疑进程
top -p <PID>

### 第 4 步：抓取相关日志
grep -R -n -i "oom|memory|killed" /var/log | head -100

## 风险点
- 直接 kill 高占用进程可能引发业务中断。

## 回滚与应急
- 先降载或切流，再重启可疑进程。
- 保留排查快照供后续复盘。

## 对应自然语言问法
- 内存突然飙高，帮我快速定位问题进程。
