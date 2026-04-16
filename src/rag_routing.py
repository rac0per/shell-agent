from typing import Optional


def detect_rag_category(user_input: str) -> Optional[str]:
    """Map user query keywords to a RAG category."""
    text = user_input.lower()
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
        )
    ):
        return "safety"
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
        )
    ):
        return "tasks"
    if any(
        k in text
        for k in (
            "bash",
            "zsh",
            "pattern",
            "差异",
            "区别",
            "confirm",
            "dry-run",
            "dry run",
        )
    ):
        return "patterns"
    if any(k in text for k in ("例子", "示例", "example", "sample")):
        return "examples"
    return "commands"