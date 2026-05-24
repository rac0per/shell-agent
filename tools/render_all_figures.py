"""
统一渲染脚本：生成论文三张 CLI 截图（HTML → PNG）

图 3-2 fig_cli_runtime     : CLI 运行界面
图 5-2 fig_safety_blocked  : 危险命令拦截与高风险确认
图 6-2 fig_exp_stepwise    : 多步任务分步执行
"""
from pathlib import Path
from html2image import Html2Image
import re
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule

OUT_DIR = Path(__file__).resolve().parent.parent / "thesis" / "template" / "pic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

hti = Html2Image(output_path=str(OUT_DIR))


def save_dark_html(console: Console, path: Path) -> None:
    """Save Rich HTML with forced dark terminal background."""
    html = path.read_text(encoding="utf-8") if path.exists() else ""
    console.save_html(str(path))
    html = path.read_text(encoding="utf-8")
    # Inject dark background override after <body
    dark_style = (
        " style='margin:0;padding:8px 12px;"
        "background:#0c0c0c;color:#d4d4d4;"
        "font-family:Consolas,\"Microsoft YaHei Mono\",\"Microsoft YaHei\",SimHei,monospace;'"
    )
    html = re.sub(r"<body([^>]*)>", f"<body{dark_style}>", html, count=1)
    path.write_text(html, encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────
# 图 3-2：CLI 运行界面（命令生成 + 确认 + 执行）
# ─────────────────────────────────────────────────────────────────────
c1 = Console(record=True, width=90)
c1.print(Panel.fit(
    "[bold cyan]Shell Agent CLI[/bold cyan]\n"
    "基于大语言模型的命令行助手，支持自然语言输入，生成 Shell 命令并提供说明。\n",
    border_style="cyan",
))
c1.print("[dim]new新建对话 | chats会话列表 | use切换对话 | delete删除对话 | session查看会话 | memory查看记忆 | clear清空记忆 | exit退出[/dim]\n")
c1.print("[dim]目标 Shell: bash[/dim]\n")
c1.print("[dim]当前会话: 对话 1 (sess-a3f2)[/dim]\n")
c1.print("[green]初始化完成[/green]\n")
c1.rule("[dim]新请求[/dim]")
c1.print("[bold]> [/bold]列出 /var/log 目录下最近修改的 5 个日志文件\n")
c1.print(Panel(
    Syntax(
        "find /var/log -maxdepth 1 -name '*.log' -printf '%T@ %p\\n'"
        " | sort -rn | head -5 | awk '{print $2}'",
        "bash", theme="monokai", line_numbers=False,
    ),
    title="[bold cyan]生成命令[/bold cyan]", border_style="cyan",
))
c1.print(Panel(
    "在 [cyan]/var/log[/cyan] 目录下搜索所有 [cyan].log[/cyan] 文件，"
    "按修改时间倒序排列，取前 5 条并打印文件路径。\n"
    "不会修改任何文件，仅读取目录元数据。",
    title="[bold cyan]命令说明[/bold cyan]", border_style="cyan",
))
c1.print(Panel(
    "[dim]（dry-run）将在 /var/log 中以只读方式枚举文件，按 mtime 排序，无写操作。[/dim]",
    title="执行预览（模拟）", border_style="blue",
))
c1.print("[bold]执行该命令？[/bold][dim]  \\[y/n][/dim]  [green]y[/green]")
c1.print()
c1.print("[green]命令已执行，返回码 0[/green]")
c1.print(Panel(
    "/var/log/syslog\n/var/log/auth.log\n/var/log/kern.log\n"
    "/var/log/dpkg.log\n/var/log/apt/history.log",
    title="执行输出", border_style="dim",
))
c1.print(Rule(style="dim"))

html1 = OUT_DIR / "fig_cli_runtime.html"
save_dark_html(c1, html1)
hti.size = (1050, 860)
hti.screenshot(html_file=str(html1), save_as="fig_cli_runtime.png")
print("OK: fig_cli_runtime.png")

# ─────────────────────────────────────────────────────────────────────
# 图 5-2：危险命令拦截与高风险确认界面
# ─────────────────────────────────────────────────────────────────────
c2 = Console(record=True, width=90)
c2.rule("[dim]场景 A  |  blocked 命令[/dim]")
c2.print()
c2.print("[bold]> [/bold]删除根目录下所有内容\n")
c2.print(Panel("rm -rf /", title="[bold cyan]生成命令[/bold cyan]", border_style="cyan"))
c2.print(Panel(
    "[red]该命令匹配黑名单规则 rm -rf /，将递归删除整个根文件系统，操作不可逆。[/red]\n\n"
    "如需执行高权限操作，请联系管理员申请权限。",
    title="命令已拦截", border_style="red",
))
c2.print(Rule(style="dim"))
c2.print()
c2.rule("[dim]场景 B  |  high 风险命令[/dim]")
c2.print()
c2.print("[bold]> [/bold]把 /home/user/project 目录权限改为 777\n")
c2.print(Panel(
    "chmod -R 777 /home/user/project",
    title="[bold cyan]生成命令[/bold cyan]", border_style="cyan",
))
c2.print(Panel(
    "[yellow]高风险命令[/yellow]\n"
    "影响范围：递归修改 /home/user/project 及其所有子目录/文件的权限位。\n"
    "将使任意用户均可读写执行该目录下的所有文件，可能导致安全漏洞。",
    title="风险警告", border_style="yellow",
))
c2.print("[bold]该命令风险较高，确认继续？[/bold][dim]  \\[y/n][/dim]  [red]n[/red]")
c2.print()
c2.print("[yellow]已取消执行。[/yellow]")
c2.print(Rule(style="dim"))

html2 = OUT_DIR / "fig_safety_blocked.html"
save_dark_html(c2, html2)
hti.size = (1050, 700)
hti.screenshot(html_file=str(html2), save_as="fig_safety_blocked.png")
print("OK: fig_safety_blocked.png")

# ─────────────────────────────────────────────────────────────────────
# 图 6-2：多步任务分步执行（三步循环）
# ─────────────────────────────────────────────────────────────────────
c3 = Console(record=True, width=90)
c3.print(Panel.fit(
    "[bold cyan]分步任务[/bold cyan]\n"
    "压缩 /var/log/myapp 日志目录，移至 /backup/，并删除 7 天前的旧备份包",
    border_style="cyan",
))
c3.print()

for step, cmd, preview, is_high in [
    (1,
     "tar -czf /tmp/myapp-logs.tar.gz /var/log/myapp",
     "（dry-run）将以只读方式打包 /var/log/myapp，写入 /tmp/myapp-logs.tar.gz。",
     False),
    (2,
     "mv /tmp/myapp-logs.tar.gz /backup/",
     "（dry-run）将 /tmp/myapp-logs.tar.gz 移动至 /backup/ 目录，原路径文件将消失。",
     False),
    (3,
     'find /backup -name "myapp-logs*.tar.gz" -mtime +7 -delete',
     "（dry-run）将匹配 /backup/myapp-logs-20250428.tar.gz 等文件并删除。",
     True),
]:
    c3.print(f"[magenta]步骤 {step}[/magenta]")
    c3.print(Panel(
        Syntax(cmd, "bash", theme="monokai", line_numbers=False),
        title="[bold cyan]生成命令[/bold cyan]", border_style="cyan",
    ))
    if is_high:
        c3.print(Panel(
            "[yellow]高风险命令[/yellow]\n"
            "影响范围：删除 /backup 下所有超过 7 天的 myapp-logs*.tar.gz 文件，不可撤销。",
            title="风险警告", border_style="yellow",
        ))
        c3.print("[bold]该命令风险较高，确认继续？[/bold][dim]  \\[y/n][/dim]  [green]y[/green]")
    c3.print(Panel(f"[dim]{preview}[/dim]", title="执行预览（模拟）", border_style="blue"))
    c3.print(f"[bold]执行该步骤命令？[/bold][dim]  \\[y/n][/dim]  [green]y[/green]")
    c3.print(f"[green]步骤 {step} 执行完毕，返回码 0[/green]")
    if step < 3:
        c3.print("[bold]继续下一步？[/bold][dim]  \\[y/n][/dim]  [green]y[/green]\n")

c3.print("[green]分步任务已完成或无需继续执行。[/green]")
c3.print(Rule(style="dim"))

html3 = OUT_DIR / "fig_exp_stepwise_case.html"
save_dark_html(c3, html3)
hti.size = (1050, 790)
hti.screenshot(html_file=str(html3), save_as="fig_exp_stepwise_case.png")
print("OK: fig_exp_stepwise_case.png")
