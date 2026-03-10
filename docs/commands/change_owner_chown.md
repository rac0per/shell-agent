# chown 属主修改命令卡

## 适用场景
- 修复部署后文件属主不正确问题。

## 用户常见问法
- 把目录属主改成 app 用户。
- 递归改属主属组。

## 推荐命令
chown appuser app.log
chown appuser:appgroup app.log
chown -R appuser:appgroup /data/app

## 参数解释
- user: 仅改属主。
- user:group: 同时改属主属组。
- -R: 递归。

## 风险与回滚
- 高风险写操作，错误属主可能导致服务不可用。
