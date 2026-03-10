# Bash 与 Zsh 差异速查

## 目标
帮助 Shell Agent 在生成命令时识别 Bash 与 Zsh 的行为差异，优先输出可兼容写法。

## 总体结论
- 大多数基础命令在 Bash 与 Zsh 中一致。
- 差异主要集中在通配符匹配、数组语法、字符串处理、启动文件与默认选项。
- 若需最大兼容性，优先使用 POSIX 风格写法并显式指定解释器。

## 启动文件差异
### Bash 常见加载文件
- 交互式登录: ~/.bash_profile 或 ~/.profile
- 交互式非登录: ~/.bashrc

### Zsh 常见加载文件
- 登录前后: ~/.zprofile 与 ~/.zlogin
- 交互配置: ~/.zshrc
- 环境变量: ~/.zshenv

建议：把别名与提示符配置放在 rc 文件，把通用环境变量放在 profile 或 zshenv（谨慎）。

## 通配符与未匹配行为
- Bash 默认：未匹配通配符通常原样保留。
- Zsh 默认：未匹配可能报错（no matches found）。

示例：
- 命令: rm *.log
- 当目录没有 .log 文件时，Zsh 可能直接报错。

兼容建议：
- 使用 find 替代裸通配符批量操作。
- 或在 Zsh 中设置 NULL_GLOB/NOMATCH 策略（仅在你明确知道影响时）。

## 数组语法差异
### Bash
arr=(a b c)
echo ${arr[0]}

### Zsh
arr=(a b c)
echo ${arr[1]}

说明：
- Bash 默认下标从 0 开始。
- Zsh 默认下标从 1 开始（可通过选项调整）。

兼容建议：
- 脚本中尽量避免依赖下标起点差异。
- 明确声明并固定解释器，例如 #!/usr/bin/env bash。

## 条件判断与 test
- 两者都支持 [ ] 与 [[ ]]。
- 复杂字符串匹配在 [[ ]] 中行为更稳妥。

兼容建议：
- 优先使用 [[ ... ]] 做字符串比较与模式匹配。
- 涉及正则时，先在目标 Shell 实测。

## 字符串替换与参数展开
两者都支持常见参数展开，但边界行为可能不同（尤其是复杂嵌套、历史扩展开关）。

兼容建议：
- 避免过于依赖 Shell 特有展开技巧。
- 复杂逻辑转为 awk 或 sed，减少方言差异。

## 历史扩展与感叹号
- Zsh 与 Bash 在交互模式都可能启用历史扩展。
- 包含 ! 的字符串在某些配置下会被意外展开。

兼容建议：
- 在脚本内优先使用单引号。
- 对含 ! 的内容进行转义或禁用历史扩展后再执行。

## 关联数组
- Bash 需较新版本并通过 declare -A。
- Zsh 语法和行为不完全一致。

兼容建议：
- 若追求跨 Shell，使用普通键值文件或 JSON/YAML 替代复杂关联数组。

## 函数定义
两者都支持 function name { ... } 与 name() { ... }，但细节选项与补全生态不同。

兼容建议：
- 脚本中使用 name() { ... } 的简洁形式。
- 减少对 shell-specific 自动补全函数的依赖。

## shebang 与执行策略
- 强烈建议在脚本首行指定解释器。
- Bash 脚本示例: #!/usr/bin/env bash
- Zsh 脚本示例: #!/usr/bin/env zsh

如果未指定 shebang 而直接 source，行为将受当前会话 Shell 影响。

## Shell Agent 生成策略建议
1. 默认输出 POSIX 兼容命令。
2. 检测到目标 Shell 为 zsh 时，避免输出依赖 Bash 0-based 数组的脚本片段。
3. 涉及批量文件操作时优先 find -print0 与 xargs -0。
4. 返回命令时附带“目标 Shell: bash/zsh”提示。

## 快速对照
- 数组下标: Bash 0 起始，Zsh 1 起始（默认）
- 未匹配通配符: Bash 多为原样保留，Zsh 可能报错
- 配置文件: Bash 偏向 bashrc/profile，Zsh 偏向 zshrc/zprofile/zshenv
- 兼容实践: 指定 shebang + POSIX 风格 + 关键命令实测

## 相关文档
- ../commands/find_large_files.md
- ../patterns/query_then_act_pattern.md
- ../safety/file_operation_safety.md
