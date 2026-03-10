# jq JSON 解析命令卡

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
