# 端口监听检查命令卡

## 文档元信息
- category: commands
- intent: port_listen_check
- risk_level: low
- target_shell: bash,zsh

## 适用场景
- 检查端口是否监听。
- 定位监听端口对应的进程与 PID。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：port listen check

## 同义问法
- 8080 端口有没有在监听？
- port listen check 标准操作。
- 哪个进程占用了 3306 端口？
- 查端口占用的命令是什么？
- 服务为什么访问不了，先查端口。

## 标准操作步骤
1. 明确端口号和协议（tcp/udp）。
2. 查询监听状态并记录 PID。
3. 验证进程名与启动参数。
4. 若未监听，回查服务日志和配置。
5. 记录排障结果到审计日志。

## 推荐命令
ss -lntp | grep :8080
ss -lunp | grep :53
lsof -nP -iTCP:8080 -sTCP:LISTEN
netstat -lntp | grep :8080

## 参数说明
- `-l`: 仅显示监听套接字。
- `-n`: 以数字方式显示端口和地址。
- `-t` / `-u`: tcp / udp。
- `-p`: 显示进程信息。

## 风险与边界
- 查询命令无写操作，但 root 权限下可见更多进程信息。
- 容器场景需在宿主机和容器内分别检查。

## 回滚方案
- 本文档为查询类操作，无回滚动作。

## 验收标准
- 可定位端口状态、PID、进程名。
- 能输出下一步排障路径（服务配置/防火墙/监听地址）。

## 关联文档
- ../tasks/service_healthcheck_sop.md
- ../commands/network_check_ping_curl.md
