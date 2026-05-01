# ps top 进程查看命令卡

## 文档元信息
- category: commands
- intent: process_inspection_ps_top
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：process inspection ps top
- 我现在要处理 process inspection ps top，该怎么做？

## 同义问法
- 看某个服务是否在运行。
- 找 CPU 占用高的进程。
- 如何查看进程状态和资源占用？
- process inspection ps top 的标准步骤。
- ps 和 top 怎么用？

## 适用场景
- 查看进程状态、资源占用与启动命令。

## 用户常见问法
- 看某个服务是否在运行。
- 找 CPU 占用高的进程。

## 推荐命令
ps -ef | grep myservice
top
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head

## 风险与回滚
- 查询命令，无写操作。
