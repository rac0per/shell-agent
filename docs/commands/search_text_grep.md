# grep 文本检索命令卡

## 文档元信息
- category: commands
- intent: search_text_grep
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：search text grep
- 我现在要处理 search text grep，该怎么做？

## 同义问法
- 全局搜索 ERROR。
- 查某个配置项在哪些文件里出现。
- 如何用 grep 搜索文本？
- search text grep 的标准步骤。
- 怎么递归搜索关键词？

## 适用场景
- 在文件或目录中搜索关键词。

## 用户常见问法
- 全局搜索 ERROR。
- 查某个配置项在哪些文件里出现。

## 推荐命令
grep -R -n "ERROR" ./logs
grep -R -n -i "timeout" .
grep -R -n -C 2 "Exception" .

## 参数解释
- -R: 递归搜索。
- -n: 显示行号。
- -i: 忽略大小写。
- -C 2: 显示前后 2 行上下文。

## 风险与回滚
- 查询命令，无写操作。
