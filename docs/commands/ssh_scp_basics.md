# ssh scp 远程操作命令卡

## 文档元信息
- category: commands
- intent: ssh_scp_basics
- risk_level: medium
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：ssh scp basics
- 我现在要处理 ssh scp basics，该怎么做？

## 同义问法
- 连接远程服务器。
- 把本地文件传到远程目录。
- 如何用 ssh 登录和 scp 传文件？
- ssh scp basics 的标准步骤。
- 怎么远程拷贝文件？

## 适用场景
- 远程登录主机与传输文件。

## 用户常见问法
- 连接远程服务器。
- 把本地文件传到远程目录。

## 推荐命令
ssh user@host
ssh -p 2222 user@host
scp ./backup.tar.gz user@host:/data/backup/
scp -P 2222 ./a.txt user@host:/tmp/

## 风险与回滚
- 涉及远程环境，需校验目标主机与账号权限。
