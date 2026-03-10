# ps top 进程查看命令卡

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
