# chmod 权限修改命令卡

## 文档元信息
- category: commands
- intent: change_permissions_chmod
- risk_level: medium
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：change permissions chmod
- 我现在要处理 change permissions chmod，该怎么做？

## 同义问法
- 让脚本可执行。
- 目录权限改成 755。
- 如何修改文件权限？
- change permissions chmod 的标准步骤。
- chmod 怎么用？

## 适用场景
- 调整脚本可执行权限或文件访问权限。

## 用户常见问法
- 让脚本可执行。
- 目录权限改成 755。

## 推荐命令
chmod +x deploy.sh
chmod 644 config.yaml
chmod -R 755 ./scripts

## 参数解释
- +x: 添加执行权限。
- 644: 文件常见读写权限。
- 755: 目录常见执行/遍历权限。
- -R: 递归修改。

## 风险与回滚
- 高风险写操作，递归前必须确认目标路径范围。
