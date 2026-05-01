# jq JSON 解析命令卡

## 文档元信息
- category: commands
- intent: json_parse_jq
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：json parse jq
- 我现在要处理 json parse jq，该怎么做？

## 同义问法
- 从 JSON 里取 code 字段。
- 美化打印 JSON。
- 如何用 jq 解析 JSON？
- json parse jq 的标准步骤。
- 怎么提取 JSON 字段？

## 适用场景
- 解析接口返回 JSON，提取字段。

## 用户常见问法
- 从 JSON 里取 code 字段。
- 美化打印 JSON。

## 推荐命令
cat result.json | jq .
cat result.json | jq -r '.code'
curl -s https://example.com/api | jq '.data.items[] | {id,name}'

## 风险与回滚
- 查询命令，无写操作；若未安装 jq 需先安装。
