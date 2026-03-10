# ping curl 网络连通性命令卡

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
