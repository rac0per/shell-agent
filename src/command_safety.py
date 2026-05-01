"""
命令安全检查模块

提供三项能力：
1. classify_command  — 白名单/黑名单分级，输出 SafetyResult
2. validate_syntax   — 语法校验（bash -n / zsh -n）
3. simulate_command  — 效果模拟（dry-run 预览）
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


# ──────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────

@dataclass
class SafetyResult:
    allowed: bool
    risk_level: str          # "low" | "medium" | "high" | "blocked"
    scope_description: str   # 对用户展示的影响范围说明
    reason: str              # blocked 时的拒绝原因；其余情况为空


# ──────────────────────────────────────────────
# 黑名单规则
# ──────────────────────────────────────────────

# 精确子串匹配（命令文本中出现即拒绝）
_BLACKLIST_PATTERNS: List[str] = [
    # 格式化磁盘
    "mkfs",
    # 磁盘直接写
    "dd of=/dev/",
    "dd if=/dev/zero",
    "dd if=/dev/urandom",
    "> /dev/sd",
    # fork 炸弹
    ":(){ :|:& };:",
    # 未授权关机/重启
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    # 权限提升
    "sudo su",
    "sudo -i",
    "sudo bash",
    "sudo sh",
    # 覆盖系统关键文件
    "> /etc/passwd",
    "> /etc/shadow",
    "> /etc/sudoers",
    "chmod 777 /",
    "chmod -R 777 /",
    "chown -R root /",
]

# 正则黑名单（优先在子串黑名单之后检查）
_BLACKLIST_REGEX: List[str] = [
    # rm -rf / 仅当路径为根（/ 后无其他路径字符）
    r"rm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+/\s*$",
    r"rm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+~/?",
    r"rm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+\*",
    r"rm\s+--no-preserve-root",
]

# 高危系统路径前缀（写操作命中即 blocked）
_PROTECTED_PATHS: List[str] = [
    "/boot", "/etc", "/bin", "/sbin",
    "/usr/bin", "/usr/sbin", "/lib", "/lib64",
    "/var/lib", "/proc", "/sys",
]

# 写操作动词（用于判断是否与受保护路径组合）
_WRITE_VERBS: List[str] = [
    "rm ", "mv ", "cp ", "chmod ", "chown ",
    "echo ", "tee ", "cat >", "dd ",
    "install ", "ln ",
]

# ──────────────────────────────────────────────
# 白名单规则
# ──────────────────────────────────────────────

# 以下开头的命令默认 low 风险，直接放行
_WHITELIST_PREFIXES: List[str] = [
    "ls", "pwd", "echo", "cat", "head", "tail",
    "grep", "find", "du", "df", "stat", "file",
    "ps", "top", "htop", "free", "uname", "uptime", "who",
    "ping", "nslookup", "dig", "host", "curl -s", "curl --silent",
    "wget --spider",
    "awk", "sed -n", "sort", "uniq", "wc", "tr", "cut",
    "git status", "git log", "git diff", "git branch",
    "git show", "git remote",
    "which", "type", "man", "help", "history",
    "env", "printenv", "id", "whoami", "groups",
    "date", "cal", "hostname",
    "ss ", "netstat", "lsof", "nmap",
    "journalctl", "dmesg",
    "python ", "python3 ", "node ", "ruby ",
]

# 受限命令：允许执行但需显示风险提示
_MEDIUM_RISK_PATTERNS: List[str] = [
    r"^rm\b(?!.*-r)(?!.*/)",          # rm 不带 -r 且无路径穿越
    r"^mv\b",
    r"^cp\b",
    r"^chmod\b",
    r"^chown\b",
    r"^systemctl\s+(restart|stop|start)\b",
    r"^service\b",
    r"^pip\b",
    r"^pip3\b",
    r"^apt\b",
    r"^yum\b",
    r"^dnf\b",
]

_HIGH_RISK_PATTERNS: List[str] = [
    r"^rm\s+-[a-zA-Z]*r",             # rm -r / rm -rf
    r"^find\s+.*-delete\b",
    r"^find\s+.*-exec\s+rm\b",
    r"^\bdd\b",
    r"^>\s*\S+",                       # 重定向覆盖
    r"\|\s*tee\b",
    r"^chmod\s+-R\b",
    r"^chown\s+-R\b",
    r"^curl\s+.*\|\s*(bash|sh)\b",    # curl pipe shell
    r"^wget\s+.*-O\s*-\s*\|",
    r"^sudo\b",
]

# ──────────────────────────────────────────────
# 影响范围描述生成
# ──────────────────────────────────────────────

def _describe_scope(command: str) -> str:
    cmd = command.strip()
    if re.search(r"\brm\b", cmd):
        return "删除操作，将移除命令指定的文件或目录（不可恢复）"
    if re.search(r"\bmv\b", cmd):
        return "移动/重命名操作，将影响源路径和目标路径下的文件"
    if re.search(r"\bchmod\b", cmd):
        return "权限变更操作，将修改目标文件或目录的访问权限"
    if re.search(r"\bchown\b", cmd):
        return "属主变更操作，将修改目标文件或目录的所有者"
    if re.search(r"\bcp\b", cmd):
        return "复制操作，将在目标路径创建或覆盖文件"
    if re.search(r"\bdd\b", cmd):
        return "磁盘读写操作，可能直接操作块设备（高风险）"
    if re.search(r"\bsystemctl\b|\bservice\b", cmd):
        return "服务控制操作，将影响系统服务的运行状态"
    if re.search(r"\b(apt|yum|dnf|pip)\b", cmd):
        return "软件包操作，将安装、升级或删除系统软件"
    if re.search(r"\bfind\b.*(-delete|-exec\s+rm)", cmd):
        return "批量查找并删除操作，将影响 find 匹配的所有文件"
    if re.search(r"\|\s*(bash|sh)\b", cmd):
        return "管道执行脚本，将在当前 shell 执行远程或动态生成的代码"
    if re.search(r"^>|>\s*\S+", cmd):
        return "重定向覆盖操作，将覆盖目标文件内容"
    return "该命令将对系统状态产生写操作"


def _hits_protected_path(command: str) -> bool:
    """检查写命令是否作用于受保护路径"""
    cmd_lower = command.lower()
    has_write_verb = any(cmd_lower.lstrip().startswith(v) for v in _WRITE_VERBS)
    if not has_write_verb:
        return False
    return any(p in command for p in _PROTECTED_PATHS)


# ──────────────────────────────────────────────
# 主分类函数
# ──────────────────────────────────────────────

def classify_command(command: str, shell: str = "bash") -> SafetyResult:
    """
    对命令进行安全分级，返回 SafetyResult。

    优先级：黑名单 > 受保护路径 > 高危 > 白名单 > 中危 > 未知
    """
    cmd = command.strip()
    if not cmd:
        return SafetyResult(
            allowed=True,
            risk_level="low",
            scope_description="",
            reason="",
        )

    # 1. 黑名单精确匹配 → blocked
    for pattern in _BLACKLIST_PATTERNS:
        if pattern in cmd:
            return SafetyResult(
                allowed=False,
                risk_level="blocked",
                scope_description="",
                reason="命中高危命令规则：'" + pattern + "'，已拒绝执行。建议改用查询命令确认目标，或联系管理员申请权限。",
            )

    # 1b. 正则黑名单
    for pattern in _BLACKLIST_REGEX:
        if re.search(pattern, cmd, re.IGNORECASE):
            return SafetyResult(
                allowed=False,
                risk_level="blocked",
                scope_description="",
                reason="命中高危命令规则（正则）：'" + pattern + "'，已拒绝执行。",
            )

    # 2. 受保护路径写操作 → blocked
    if _hits_protected_path(cmd):
        return SafetyResult(
            allowed=False,
            risk_level="blocked",
            scope_description="",
            reason="命令涉及对系统保护路径（/etc、/bin 等）的写操作，已拒绝执行。",
        )

    # 3. 高危模式 → allowed=True 但 risk=high，需二次确认
    for pattern in _HIGH_RISK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return SafetyResult(
                allowed=True,
                risk_level="high",
                scope_description=_describe_scope(cmd),
                reason="",
            )

    # 4. 白名单前缀 → low
    cmd_lower = cmd.lower()
    for prefix in _WHITELIST_PREFIXES:
        if cmd_lower.startswith(prefix.lower()):
            return SafetyResult(
                allowed=True,
                risk_level="low",
                scope_description="",
                reason="",
            )

    # 5. 中危模式 → medium
    for pattern in _MEDIUM_RISK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return SafetyResult(
                allowed=True,
                risk_level="medium",
                scope_description=_describe_scope(cmd),
                reason="",
            )

    # 6. 未识别命令 → blocked（超出白名单）
    return SafetyResult(
        allowed=False,
        risk_level="blocked",
        scope_description="",
        reason="命令 '" + cmd.split()[0] + "' 不在允许列表中，已拒绝执行。如需执行，请联系管理员申请权限。",
    )


# ──────────────────────────────────────────────
# 语法校验
# ──────────────────────────────────────────────

def _fallback_validate_syntax(command: str) -> tuple[bool, str]:
    """Best-effort syntax check used when bash/zsh is unavailable."""
    cmd = command.strip()
    if not cmd:
        return True, ""

    # Detect unbalanced command substitution: $( ... )
    cmdsub_depth = 0
    i = 0
    while i < len(cmd):
        if cmd[i] == "\\":
            i += 2
            continue
        if cmd[i:i + 2] == "$(":
            cmdsub_depth += 1
            i += 2
            continue
        if cmd[i] == ")" and cmdsub_depth > 0:
            cmdsub_depth -= 1
        i += 1
    if cmdsub_depth != 0:
        return False, "语法错误：未闭合的命令替换 $(...)"

    # Detect unclosed quotes.
    in_single = False
    in_double = False
    escaped = False
    for ch in cmd:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
    if in_single or in_double:
        return False, "语法错误：存在未闭合的引号"

    # Detect clearly broken for-in loops such as: for x in; do ...; done
    if re.search(r"\bfor\s+\w+\s+in\s*;", cmd):
        return False, "语法错误：for ... in 语句缺少迭代列表"

    return True, ""

def validate_syntax(command: str, shell: str = "bash") -> tuple[bool, str]:
    """
    通过 shell -n 检验命令语法是否合法。
    返回 (ok, error_message)；error_message 在 ok=True 时为空字符串。
    """
    shell_exec = "bash" if shell not in ("bash", "zsh") else shell
    try:
        result = subprocess.run(
            [shell_exec, "-n", "-c", command],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, ""
        err = (result.stderr or "").strip() or "语法错误（无详细信息）"
        return False, err
    except FileNotFoundError:
        # shell 不可用时使用轻量兜底校验
        return _fallback_validate_syntax(command)
    except subprocess.TimeoutExpired:
        return _fallback_validate_syntax(command)


# ──────────────────────────────────────────────
# 效果模拟（dry-run 预览）
# ──────────────────────────────────────────────

def simulate_command(command: str, shell: str = "bash") -> str:
    """
    对命令生成 dry-run 预览输出（只读，不实际修改文件系统）。
    返回预览文本字符串。
    """
    cmd = command.strip()
    if not cmd:
        return ""

    # rm → 用 find 替换，显示将被删除的文件
    rm_match = re.match(
        r"rm\s+(-[a-zA-Z]*\s+)*(?P<target>.+)$", cmd
    )
    if rm_match:
        target = rm_match.group("target").strip()
        preview_cmd = f"find {target} -maxdepth 3 2>/dev/null | head -20"
        return _run_readonly(preview_cmd, shell, prefix="[预览] 将被删除的文件：")

    # find -delete → 去掉 -delete 只做查找
    if re.search(r"\bfind\b", cmd) and "-delete" in cmd:
        preview_cmd = re.sub(r"\s*-delete\b", "", cmd)
        return _run_readonly(preview_cmd, shell, prefix="[预览] find 将匹配的文件：")

    # chmod/chown → stat 目标
    perm_match = re.match(r"(chmod|chown)\s+\S+\s+(?P<target>.+)$", cmd)
    if perm_match:
        target = perm_match.group("target").strip()
        preview_cmd = f"stat {target} 2>/dev/null || ls -la {target} 2>/dev/null"
        return _run_readonly(preview_cmd, shell, prefix="[预览] 目标文件当前权限/属主：")

    # mv → 显示源文件信息
    mv_match = re.match(r"mv\s+(?P<src>\S+)\s+(?P<dst>\S+)$", cmd)
    if mv_match:
        src = mv_match.group("src")
        dst = mv_match.group("dst")
        return f"[预览] 将把 {src} 移动到 {dst}（目标若存在将被覆盖）"

    # cp → 显示源文件信息
    cp_match = re.match(r"cp\s+(-[a-zA-Z]+\s+)*(?P<src>\S+)\s+(?P<dst>\S+)$", cmd)
    if cp_match:
        src = cp_match.group("src")
        dst = cp_match.group("dst")
        return f"[预览] 将把 {src} 复制到 {dst}"

    # 其他：echo dry-run
    return f"[预览] {cmd}"


def _run_readonly(cmd: str, shell: str, prefix: str = "") -> str:
    shell_exec = "bash" if shell not in ("bash", "zsh") else shell
    try:
        result = subprocess.run(
            [shell_exec, "-c", cmd],
            capture_output=True,
            text=True,
            timeout=8,
        )
        output = (result.stdout or "").strip()
        if not output:
            output = "(无匹配内容)"
        return f"{prefix}\n{output}" if prefix else output
    except Exception:
        return f"{prefix}(预览执行失败)"
