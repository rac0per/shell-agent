# 解压归档命令卡

## 文档元信息
- category: commands
- intent: extract_archives
- risk_level: medium
- target_shell: bash,zsh

## 适用场景
- 解压 tar.gz、tar、zip 文件到指定目录。
- 恢复备份包并核对文件完整性。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：extract archives

## 同义问法
- 解压 tar.gz 到指定目录。
- extract archives 的标准步骤。
- 把压缩包解到 /data/restore。
- unzip 到当前目录怎么操作？
- 如何先预览再解压？

## 标准操作步骤
1. 识别归档类型：`file archive.xxx` 确认是 tar.gz 或 zip。
2. 预览内容：`tar -tzf` 或 `unzip -l` 检查目标文件名。
3. 创建目标目录：`mkdir -p /data/restore`。
4. 执行解压：按类型使用 tar 或 unzip。
5. 校验结果：检查文件数、权限与目录结构。

## 推荐命令
tar -tzf backup.tar.gz | head -30
tar -xzf backup.tar.gz -C /data/restore
unzip -l report.zip
unzip report.zip -d /data/restore

## 参数说明
- `-t`: 列出归档内容。
- `-x`: 解包。
- `-z`: gzip 格式。
- `-f`: 指定归档文件。
- `-C`: 指定目标目录。

## 风险与边界
- 解压时可能覆盖同名文件，建议先清空或隔离目标目录。
- 不可信归档可能包含路径穿越，先预览内容再执行。

## 回滚方案
- 解压前备份目标目录元数据。
- 回滚时删除本次新增目录并恢复备份。

## 验收标准
- 目标目录文件完整、无异常覆盖。
- 应用可从解压目录正常读取所需文件。

## 关联文档
- ../tasks/config_backup_restore_sop.md
- ../safety/pre_execution_validation_checklist.md
