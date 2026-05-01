# 证书过期检查 SOP

## 文档元信息
- category: tasks
- intent: certificate_expiry_check
- risk_level: none
- target_shell: bash,zsh

## 适用场景
- 检查 TLS/SSL 证书到期时间，提前预警。
- 批量巡检域名证书有效期。
- 记录证书检查结果到巡检日志。

## 覆盖失败 Query
- 给我这份文档的标准操作步骤：certificate expiry check
- 我现在要处理 certificate expiry check，该怎么做？

## 同义问法
- 帮我查这个域名证书多久过期。
- 如何检查 SSL 证书有效期？
- certificate expiry check 的标准步骤。
- TLS 证书什么时候到期，怎么查？
- 证书过期检查 SOP 是什么？

## 任务目标
提前发现 TLS 证书即将过期风险，避免服务中断。

## 前置检查
- 确认证书域名与端口。
- 确认检查周期与告警阈值（如 30 天）。

## 操作步骤
### 第 1 步：查看证书到期时间
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -dates

### 第 2 步：提取 notAfter
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -enddate

### 第 3 步：记录结果到巡检日志
echo "$(date '+%F %T') example.com cert checked" >> /var/log/cert_check.log

## 风险点
- 外网连接受限环境可能返回空结果。

## 回滚与应急
- 即将过期时提前申请新证书并灰度替换。
- 证书切换后执行健康检查与握手验证。

## 对应自然语言问法
- 帮我查这个域名证书多久过期。
