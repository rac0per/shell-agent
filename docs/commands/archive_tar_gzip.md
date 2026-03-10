# tar gzip 压缩归档命令卡

## 适用场景
- 备份目录或日志归档。

## 用户常见问法
- 把这个目录打包压缩。
- 按日期生成归档文件。

## 推荐命令
tar -czf backup_20260310.tar.gz /data/project
tar -czf logs.tar.gz /var/log/app

## 参数解释
- -c: 创建归档。
- -z: 使用 gzip。
- -f: 指定输出文件。

## 风险与回滚
- 写入新归档文件，注意目标磁盘空间。
