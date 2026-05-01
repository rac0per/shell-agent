# cp 保留权限复制命令卡

## 文档元信息
- category: commands
- intent: copy_with_permissions
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 复制目录到备份路径，并保留权限、时间戳、属主信息。
- 迁移配置目录时，避免权限丢失导致服务启动失败。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：copy with permissions
- 我现在要处理 copy with permissions，该怎么做？

## 同义问法
- 保留权限复制目录怎么做？
- cp 怎样保留时间戳和权限？
- 复制到备份目录并保留属主。
- copy with permissions 的标准步骤。
- 如何安全复制并避免覆盖线上文件？

## 标准操作步骤
1. 查询源目录权限：`ls -l` 或 `stat` 先确认源文件属性。
2. 预演目标覆盖风险：先用 `cp -ain` 或 `rsync -an` 预览。
3. 执行复制：按最小范围执行 `cp -a` 或 `rsync -a`。
4. 校验属性：比对文件数、权限、属主和时间戳。
5. 记录日志：记录源路径、目标路径、执行时间和操作者。

## 推荐命令
cp -a /data/app /data/app_bak
cp -ain /data/app /data/app_bak
rsync -aHAX --info=stats2 /data/app/ /data/app_bak/

## 参数说明
- `-a`: 归档模式，保留权限、时间戳、软链接等。
- `-i`: 覆盖前交互确认。
- `-n`: 不覆盖已存在文件。

## 风险与边界
- 禁止直接覆盖生产关键目录（如 `/etc`, `/var/lib`）。
- 大目录复制会产生 I/O 峰值，建议低峰执行。
- 跨文件系统复制时，ACL 或扩展属性可能不完整。

## 回滚方案
- 复制前先生成目标目录快照或备份。
- 若误覆盖，优先从备份目录恢复：`rsync -a --delete <backup>/ <target>/`。

## 验收标准
- 文件数量一致，关键配置文件权限一致。
- 服务进程可正常读取目标目录。

## 关联文档
- ../safety/file_operation_safety.md
- ../tasks/config_backup_restore_sop.md
