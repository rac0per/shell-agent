# tail 实时日志命令卡

## 文档元信息
- category: commands
- intent: tail_logs_realtime
- risk_level: none
- target_shell: bash,zsh

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：tail logs realtime
- 我现在要处理 tail logs realtime，该怎么做？

## 同义问法
- 实时看日志。
- 只看最后 200 行并持续跟踪。
- 如何实时跟踪日志输出？
- tail logs realtime 的标准步骤。
- tail -f 怎么用？

## 适用场景
- 实时观察服务日志输出。

## 用户常见问法
- 实时看日志。
- 只看最后 200 行并持续跟踪。

## 推荐命令
tail -n 200 app.log
tail -f app.log
tail -n 100 -f /var/log/syslog

## 参数解释
- -n 200: 显示最后 200 行。
- -f: 持续跟随新日志。

## 风险与回滚
- 查询命令，无写操作。
