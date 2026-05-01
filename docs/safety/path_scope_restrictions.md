# 路径范围限制策略

## 文档元信息
- category: safety
- intent: path_scope_restrictions
- risk_level: high
- target_shell: bash,zsh

## 适用场景
- 限制 Shell Agent 命令只作用于授权目录。
- 防止路径穿越和软链接绕过。
- 配置路径白名单与拒绝规则。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：path scope restrictions
- 我现在要处理 path scope restrictions，该怎么做？

## 同义问法
- 如何限制命令作用的路径范围？
- 路径白名单怎么配置？
- path scope restrictions 的标准步骤。
- 怎么防止操作扩散到系统目录？
- 路径范围限制策略是什么？

## 目标
限制命令仅作用于授权路径，避免误操作扩散到系统或他人目录。

## 允许路径示例
- /data/app
- /data/backup
- /tmp/app
- 项目工作目录

## 禁止路径示例
- /
- /etc
- /bin
- /usr
- /boot
- /var/lib
- 用户主目录之外的未授权路径

## 判定规则
1. 执行前将相对路径转换为绝对路径。
2. 解析软链接后再做路径前缀校验。
3. 路径不在 allowlist 则直接拒绝。

## 边界风险
- ../../ 目录穿越。
- 软链接跳转绕过。
- 环境变量展开后越界。

## 防护建议
- 统一使用 realpath 后判定。
- 禁止通配符直接命中根路径。
- 对批量命令强制输出实际命中文件清单。

## 相关文档
- command_whitelist_policy.md
- pre_execution_validation_checklist.md
