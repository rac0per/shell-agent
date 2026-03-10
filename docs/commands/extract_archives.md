# 解压归档命令卡

## 适用场景
- 解压 tar.gz、zip 文件。

## 用户常见问法
- 解压这个压缩包到当前目录。
- 指定目录解压。

## 推荐命令
tar -xzf backup.tar.gz
tar -xzf backup.tar.gz -C /data/restore
unzip report.zip -d ./report

## 参数解释
- -x: 解包。
- -z: gzip 格式。
- -f: 归档文件。
- -C: 指定目标目录。

## 风险与回滚
- 解压会写入文件，先确认目标目录空闲空间。
