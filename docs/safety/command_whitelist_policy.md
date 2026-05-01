# 命令白名单策略

## 文档元信息
- category: safety
- intent: command_whitelist_policy
- risk_level: high
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：command whitelist policy
- 我现在要处理 command whitelist policy，该怎么做？

## 同义问法
- 哪些命令是允许执行的？
- 如何配置命令白名单？
- command whitelist policy 的标准步骤。
- 白名单策略怎么维护？
- 如何只允许安全命令执行？

## 目标
仅允许明确审计过的命令进入执行阶段，降低未知风险。

## 建议默认白名单
- 查询类：ls, pwd, cat, head, tail, grep, find, du, df
- 网络诊断：ping, nslookup, curl 只读请求
- 文本处理：awk, sed 只读模式, sort, uniq
- 版本控制只读：git status, git log, git diff

## 受限白名单
以下命令需满足附加条件后才允许：
- rm: 仅允许在临时目录，且不得带 -rf
- mv: 仅允许在业务工作目录内
- chmod: 禁止递归修改系统目录
- systemctl: 默认仅 status，不允许 restart 或 stop

## 策略实现建议
1. 先判定命令主程序是否在白名单。
2. 再判定参数组合是否在允许集合。
3. 最后判定作用路径是否在允许范围。

## 拒绝与引导
- 当前命令不在白名单，禁止执行。
- 可用替代：先执行查询命令确认目标，再提交审批执行高风险操作。

## 维护机制
- 每月审计白名单命令使用频率与误拒率。
- 新增白名单需记录申请人、用途、回滚方案。

## 相关文档
- command_blacklist_policy.md
- path_scope_restrictions.md
