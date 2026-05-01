# 临时文件清理任务 SOP

## 文档元信息
- category: tasks
- intent: temp_file_cleanup
- risk_level: medium
- target_shell: bash,zsh

## 任务目标
- 清理过期临时文件，释放空间并降低误删风险。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：temp file cleanup

## 同义问法
- temp file cleanup 标准流程。
- 清理 3 天前临时文件但先别直接删。
- 做一个安全的临时目录清理方案。
- /tmp 文件太多怎么处理？
- 先隔离再删除的清理步骤。

## 标准操作步骤
1. 查询候选文件并保存清单。
2. 预演确认数量与路径范围。
3. 先移动到隔离目录，不直接删除。
4. 观察一段时间后再清理隔离目录。
5. 记录释放空间与回滚窗口。

## 推荐命令
find /tmp -type f -mtime +3 -print > /tmp/tmp_cleanup_candidates.txt
find /tmp -type f -mtime +3 -print
mkdir -p /tmp/quarantine && find /tmp -type f -mtime +3 -exec mv {} /tmp/quarantine/ \;
find /tmp/quarantine -type f -mtime +7 -delete

## 风险与边界
- 临时目录中可能有正在被进程占用的文件。
- 批量移动存在重名冲突，建议保留目录结构或增加前缀。

## 回滚方案
- 从 `/tmp/quarantine` 按清单恢复文件。
- 回滚后重启受影响任务并验证。

## 验收标准
- 空间释放达到预期。
- 无业务任务因清理失败。

## 关联文档
- ../commands/find_and_delete_tmp.md
- ../patterns/query_then_act_pattern.md
- ../safety/dry_run_and_confirmation.md
