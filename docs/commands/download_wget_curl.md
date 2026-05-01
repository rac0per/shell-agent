# wget curl 下载命令卡

## 文档元信息
- category: commands
- intent: download_wget_curl
- risk_level: low
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：download wget curl
- 我现在要处理 download wget curl，该怎么做？

## 同义问法
- 下载这个文件到当前目录。
- 指定文件名保存。
- 如何用 wget 或 curl 下载文件？
- download wget curl 的标准步骤。
- 怎么下载远程文件？

## 适用场景
- 下载脚本、压缩包或测试文件。

## 用户常见问法
- 下载这个文件到当前目录。
- 指定文件名保存。

## 推荐命令
wget https://example.com/file.tar.gz
curl -LO https://example.com/file.tar.gz
curl -L https://example.com/file.tar.gz -o app.tar.gz

## 风险与回滚
- 写入本地文件，来源需可信并校验哈希。
