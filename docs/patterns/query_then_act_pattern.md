# 先查询后执行模式（Query Then Act）

## 模式目标
将高风险操作拆成两步：先查询候选，再执行动作，降低误操作概率。

## 适用场景
- 批量删除。
- 批量移动或重命名。
- 批量压缩或归档。

## 标准流程
1. 查询阶段：用 find 或 grep 精准筛选目标。
2. 预览阶段：用 echo 或 ls 验证将要处理的对象。
3. 执行阶段：确认后再执行 rm 或 mv 或 gzip。
4. 记录阶段：保存执行日志用于追溯。

## 模板示例
### 删除 7 天前临时文件
查询：find /tmp -type f -mtime +7 -name "*.tmp"
预览：find /tmp -type f -mtime +7 -name "*.tmp" -print
执行：find /tmp -type f -mtime +7 -name "*.tmp" -delete

### 移动大文件到归档目录
查询：find /data -type f -size +500M
预览：find /data -type f -size +500M -print
执行：find /data -type f -size +500M -exec mv {} /data/archive/ \;

## 风险控制要点
- 执行前必须保留查询命令结果快照。
- 目标路径必须使用绝对路径。
- 处理文件名含空格时使用 -print0 与 xargs -0。

## 相关文档
- ../safety/file_operation_safety.md
- ../tasks/log_cleanup_sop.md
