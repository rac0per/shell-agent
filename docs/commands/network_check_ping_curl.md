# ping curl 网络连通性命令卡

## 文档元信息
- category: commands
- intent: network_check_ping_curl
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：network check ping curl
- 我现在要处理 network check ping curl，该怎么做？

## 同义问法
- 网络通不通。
- 接口是否返回 200。
- 如何检查网络连通性？
- network check ping curl 的标准步骤。
- 怎么验证 HTTP 服务可用？

## 适用场景
- 快速验证网络连通与 HTTP 服务可用性。

## 用户常见问法
- 网络通不通。
- 接口是否返回 200。

## 推荐命令
ping -c 4 example.com
curl -I https://example.com
curl -s -o /dev/null -w "%{http_code}\n" https://example.com/api/health

## 风险与回滚
- 查询命令，无写操作。
