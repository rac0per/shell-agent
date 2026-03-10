# find 大文件检索命令卡

## 适用场景
- 快速定位当前目录或指定目录下体积较大的文件。
- 排查磁盘占用异常。
- 给后续归档、压缩、删除提供候选文件列表。

## 用户常见问法
- 帮我找出当前目录超过 100MB 的文件。
- 看一下 /var/log 下有哪些大文件。
- 找最近 7 天内大于 200MB 的日志文件。

## 推荐命令
### 仅查当前目录（含子目录）大于 100MB 的文件
find . -type f -size +100M

### 查指定目录并按大小排序（可读化）
find /var/log -type f -size +50M -print0 | xargs -0 du -h | sort -hr

### 查最近 7 天修改且大于 200MB 的文件
find /var/log -type f -mtime -7 -size +200M

## 参数解释
- -type f: 仅匹配普通文件。
- -size +100M: 文件大于 100MB。
- -mtime -7: 最近 7 天内修改。
- -print0 与 xargs -0: 处理包含空格的文件名更安全。

## 风险与回滚
- 仅查询命令本身无写操作，风险低。
- 若后续接删除命令，建议先把结果重定向保存。

## 示例输入输出
输入：查 /data 下大于 1GB 文件。
命令：find /data -type f -size +1G
输出：返回文件路径列表。

## 相关文档
- ../patterns/query_then_act_pattern.md
- ../safety/file_operation_safety.md
