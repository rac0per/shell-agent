# mv 移动与重命名命令卡

## 文档元信息
- category: commands
- intent: move_and_rename
- risk_level: high
- target_shell: bash,zsh

## 适用场景
- 对文件进行重命名。
- 批量移动日志或归档文件到目标目录。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：move and rename

## 同义问法
- move and rename 怎么做？
- 把日志安全移动到 archive 目录。
- 批量重命名文件避免误操作。
- mv 的标准 SOP。
- 改名和迁移文件的步骤。

## 标准操作步骤
1. 查询候选对象：用 `find` 或 `ls` 确认范围。
2. 预演动作：使用 `echo mv ...` 先输出将执行的命令。
3. 执行移动：先小范围执行，再全量。
4. 校验结果：检查目标目录文件数量和命名。
5. 记录与审计：记录处理数量和失败条目。

## 推荐命令
mv old.log new.log
mkdir -p /data/archive && mv *.log /data/archive/
find /var/log -type f -name "*.log" -mtime +7 -print
find /var/log -type f -name "*.log" -mtime +7 -exec mv {} /data/archive/ \;

## 参数说明
- `mv src dst`: 同目录为重命名，跨目录为移动。
- `-i`: 覆盖前确认。
- `-n`: 不覆盖同名文件。

## 风险与边界
- 批量移动存在误匹配风险，必须先预览。
- 跨分区移动可能耗时长，建议低峰执行。

## 回滚方案
- 执行前导出候选清单。
- 回滚时按清单 `mv` 回原路径。

## 验收标准
- 目标目录文件数量符合预期。
- 无关键业务文件误移动。

## 关联文档
- ../patterns/query_then_act_pattern.md
- ../safety/dry_run_and_confirmation.md
