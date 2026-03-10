# wget curl 下载命令卡

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
