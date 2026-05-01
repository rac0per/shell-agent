# du 与 df 磁盘分析命令卡

## 文档元信息
- category: commands
- intent: disk_usage_du_df
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：disk usage du df
- 我现在要处理 disk usage du df，该怎么做？

## 同义问法
- 磁盘快满了，哪里占用大。
- 看每个子目录大小并排序。
- 如何查看磁盘使用情况？
- disk usage du df 的标准步骤。
- du 和 df 怎么用？

## 适用场景
- 查看磁盘总体使用率与目录占用。

## 用户常见问法
- 磁盘快满了，哪里占用大。
- 看每个子目录大小并排序。

## 推荐命令
df -h
du -sh ./* | sort -hr
du -sh /var/log/* | sort -hr

## 参数解释
- df -h: 查看各挂载点空间。
- du -sh: 统计目录总大小。
- sort -hr: 人类可读数值降序。

## 风险与回滚
- 查询命令，无写操作。
