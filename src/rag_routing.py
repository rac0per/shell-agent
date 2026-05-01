from typing import Optional


def detect_rag_category(user_input: str) -> Optional[str]:
    """Map user query keywords to a RAG category.

    Order matters: checks are evaluated top-to-bottom and return on first match.
    Specific phrases are checked before broad single-word triggers to avoid
    cross-category false positives (e.g. "安全导出" must beat "安全").
    """
    text = user_input.lower()

    # ── Pre-checks: specific task phrases that contain safety-sounding words ──
    # Must run before the safety block so "安全导出" doesn't misroute to safety.
    if any(k in text for k in ("安全导出", "导出日志", "日志导出")):
        return "tasks"

    # ── Archive/compression commands ──────────────────────────────────────────
    # Must run before the tasks block so "tar.gz 备份文件" doesn't misroute to tasks.
    if "tar.gz" in text or ("tar " in text and "gz" in text):
        return "commands"

    # ── Safety: policies, access control, blacklists, dry-run confirmations ──
    if any(
        k in text
        for k in (
            "安全",
            "危险",
            "风险",
            "禁止",
            "safe",
            "danger",
            "permission",
            "sudo",
            "root",
            "blacklist",
            "whitelist",
            "黑名单",
            "白名单",
            "越权",
            "权限控制",
            "权限级别",
            "模拟运行",
            "绝对不能",
            "dry-run",
            "dry run",
            "审计",
        )
    ):
        return "safety"

    # ── Tasks: SOP workflows and multi-step operational procedures ────────────
    if any(
        k in text
        for k in (
            "sop",
            "流程",
            "步骤",
            "备份",
            "恢复",
            "证书",
            "磁盘容量",
            "task",
            "procedure",
            "backup",
            "restore",
            "certificate",
            "内存",
            "巡检",
            "健不健康",
            "定时任务",
            "旧日志",
            "日志目录",
            "日志清理",
        )
    ):
        return "tasks"

    # ── Patterns: shell compatibility and safe-execution design patterns ──────
    if any(
        k in text
        for k in (
            "bash",
            "zsh",
            "pattern",
            "差异",
            "区别",
            "confirm",
            "预览",
        )
    ):
        return "patterns"

    if any(k in text for k in ("例子", "示例", "example", "sample")):
        return "examples"

    return "commands"