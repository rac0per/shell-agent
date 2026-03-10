# ssh scp 远程操作命令卡

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
