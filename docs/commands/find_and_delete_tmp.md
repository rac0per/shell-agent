# 查找并清理临时文件命令卡

## 适用场景
- 清理历史临时文件释放空间。

## 用户常见问法
- 删除 7 天前的 tmp 文件。
- 先看要删哪些再执行。

## 推荐命令
find /tmp -type f -name "*.tmp" -mtime +7
find /tmp -type f -name "*.tmp" -mtime +7 -print
find /tmp -type f -name "*.tmp" -mtime +7 -delete

## 风险与回滚
- 删除操作不可逆，建议先移动到隔离目录再延迟删除。
