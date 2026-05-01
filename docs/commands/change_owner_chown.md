# chown 属主修改命令卡

## 文档元信息
- category: commands
- intent: change_owner_chown
- risk_level: medium
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：change owner chown
- 我现在要处理 change owner chown，该怎么做？

## 同义问法
- 把目录属主改成 app 用户。
- 递归改属主属组。
- 如何修改文件所有者？
- change owner chown 的标准步骤。
- chown 怎么用？
- 部署完发现文件所有者不对，批量改成 www-data。
- 文件属主设置不正确，怎么批量修复。
- 把所有文件的 owner 改成指定用户。

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
