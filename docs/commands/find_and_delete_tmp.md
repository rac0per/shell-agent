# 查找并清理临时文件命令卡

## 文档元信息
- category: commands
- intent: find_and_delete_tmp
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 清理历史临时文件释放磁盘空间。
- 查找并删除超过指定天数的 tmp 文件。
- 先预览再安全删除，避免误删。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：find and delete tmp
- 我现在要处理 find and delete tmp，该怎么做？

## 同义问法
- 删除 7 天前的 tmp 文件。
- 先看要删哪些再执行。
- 如何查找并清理临时文件？
- find and delete tmp 的标准步骤。
- 怎么安全地批量删除临时文件？
- 清理 /tmp 目录下的过期文件。

## 标准操作步骤
1. 预览候选文件（不删除）：`find /tmp -type f -name "*.tmp" -mtime +7 -print`
2. 确认文件数量可接受后执行删除：`find /tmp -type f -name "*.tmp" -mtime +7 -delete`
3. 验证清理结果：`find /tmp -type f -name "*.tmp" -mtime +7 | wc -l`

## 推荐命令
find /tmp -type f -name "*.tmp" -mtime +7
find /tmp -type f -name "*.tmp" -mtime +7 -print
find /tmp -type f -name "*.tmp" -mtime +7 -delete

## 参数说明
- `-type f`：只匹配文件，不包含目录。
- `-name "*.tmp"`：匹配以 .tmp 结尾的文件。
- `-mtime +7`：最后修改时间超过 7 天。
- `-print`：打印匹配路径（预览模式）。
- `-delete`：直接删除，不可恢复。

## 风险与边界
- 删除操作不可逆，必须先用 `-print` 预览确认。
- 建议先移动到隔离目录再延迟删除：`-exec mv {} /tmp/to_delete/ \;`
- 不要对 `/` 或 `/etc` 等系统路径执行 `-delete`。

## 回滚方案
- 若误删，从备份恢复；无备份则不可恢复。
- 建议先 `mv` 到隔离目录，确认无误后再 `rm`。

## 验收标准
- `-print` 输出结果符合预期范围。
- 删除后 `-mtime +7` 无命中结果。

## 关联文档
- ../tasks/temp_file_cleanup_sop.md
- ../tasks/disk_capacity_emergency_sop.md
