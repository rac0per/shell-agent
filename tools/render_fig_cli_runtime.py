"""
生成图 3-2：系统CLI运行界面实拍（fig:cli-runtime）
展示：启动面板 -> 用户输入自然语言 -> 模型生成命令 -> 执行预览 -> 用户确认
"""
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule

OUT_DIR = Path(__file__).resolve().parent.parent / "thesis" / "template" / "pic"
OUT_FILE = OUT_DIR / "fig_cli_runtime.png"

os.makedirs(OUT_DIR, exist_ok=True)

console = Console(record=True, width=88)

# ── 启动面板 ──────────────────────────────────────────────────────────
console.print(
    Panel.fit(
        "[bold cyan]Shell Agent CLI[/bold cyan]\n"
        "基于大语言模型的命令行助手，支持自然语言输入，生成Shell命令并提供说明。\n",
        border_style="cyan",
    )
)
console.print(
    "[dim]new新建对话 | chats会话列表 | use切换对话 | delete删除对话 | session查看会话 | memory查看记忆 | clear清空记忆 | exit退出[/dim]\n"
)
console.print("[dim]目标 Shell: bash[/dim]\n")
console.print("[dim]当前会话: 对话 1 (sess-a3f2)[/dim]\n")
console.print("[green]初始化完成[/green]\n")

# ── 用户输入 ──────────────────────────────────────────────────────────
console.rule("[dim]新请求[/dim]")
console.print("[bold]> [/bold]列出 /var/log 目录下最近修改的5个日志文件\n")

# ── 模型响应：命令 + 说明 ─────────────────────────────────────────────
console.print(
    Panel(
        Syntax(
            "find /var/log -maxdepth 1 -name '*.log' -printf '%T@ %p\\n' "
            "| sort -rn | head -5 | awk '{print $2}'",
            "bash",
            theme="monokai",
            line_numbers=False,
        ),
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)
console.print(
    Panel(
        "在 [cyan]/var/log[/cyan] 目录下搜索所有 [cyan].log[/cyan] 文件，"
        "按修改时间倒序排列，取前 5 条并打印文件路径。\n"
        "不会修改任何文件，仅读取目录元数据。",
        title="[bold cyan]命令说明[/bold cyan]",
        border_style="cyan",
    )
)

# ── 执行预览（模拟） ───────────────────────────────────────────────────
console.print(
    Panel(
        "[dim]（dry-run）将在 /var/log 中以只读方式枚举文件，按 mtime 排序，无写操作。[/dim]",
        title="执行预览（模拟）",
        border_style="blue",
    )
)

# ── 用户确认 ──────────────────────────────────────────────────────────
console.print("[bold]执行该命令? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print()
console.print("[green]命令已执行，返回码 0[/green]")
console.print(
    Panel(
        "/var/log/syslog\n"
        "/var/log/auth.log\n"
        "/var/log/kern.log\n"
        "/var/log/dpkg.log\n"
        "/var/log/apt/history.log",
        title="执行输出",
        border_style="dim",
    )
)
console.print(Rule(style="dim"))

html_path = OUT_DIR / "fig_cli_runtime.html"
console.save_html(str(html_path))
print(f"HTML saved → {html_path}")


# ── 启动面板 ──────────────────────────────────────────────────────────
console.print(
    Panel.fit(
        "[bold cyan]Shell Agent CLI[/bold cyan]\n"
        "基于大语言模型的命令行助手，支持自然语言输入，生成Shell命令并提供说明。\n",
        border_style="cyan",
    )
)
console.print(
    "[dim]new新建对话 | chats会话列表 | use切换对话 | delete删除对话 | session查看会话 | memory查看记忆 | clear清空记忆 | exit退出[/dim]\n"
)
console.print("[dim]目标 Shell: bash[/dim]\n")
console.print("[dim]当前会话: 对话 1 (sess-a3f2)[/dim]\n")
console.print("[green]初始化完成[/green]\n")

# ── 用户输入 ──────────────────────────────────────────────────────────
console.rule("[dim]新请求[/dim]")
console.print("[bold]> [/bold]列出 /var/log 目录下最近修改的5个日志文件\n")

# ── 模型响应：命令 + 说明 ─────────────────────────────────────────────
console.print(
    Panel(
        Syntax(
            "find /var/log -maxdepth 1 -name '*.log' -printf '%T@ %p\\n' "
            "| sort -rn | head -5 | awk '{print $2}'",
            "bash",
            theme="monokai",
            line_numbers=False,
        ),
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)
console.print(
    Panel(
        "在 [cyan]/var/log[/cyan] 目录下搜索所有 [cyan].log[/cyan] 文件，"
        "按修改时间倒序排列，取前 5 条并打印文件路径。\n"
        "不会修改任何文件，仅读取目录元数据。",
        title="[bold cyan]命令说明[/bold cyan]",
        border_style="cyan",
    )
)

# ── 执行预览（模拟） ───────────────────────────────────────────────────
console.print(
    Panel(
        "[dim]（dry-run）将在 /var/log 中以只读方式枚举文件，按 mtime 排序，无写操作。[/dim]",
        title="执行预览（模拟）",
        border_style="blue",
    )
)

# ── 用户确认 ──────────────────────────────────────────────────────────
console.print("[bold]执行该命令? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print()
console.print("[green]命令已执行，返回码 0[/green]")
console.print(
    Panel(
        "/var/log/syslog\n"
        "/var/log/auth.log\n"
        "/var/log/kern.log\n"
        "/var/log/dpkg.log\n"
        "/var/log/apt/history.log",
        title="执行输出",
        border_style="dim",
    )
)
console.print(Rule(style="dim"))

svg_path = OUT_DIR / "fig_cli_runtime.svg"
console.save_svg(str(svg_path), title="Shell Agent CLI")
print(f"SVG saved → {svg_path}")

# ── SVG → PNG (via cairosvg or PIL fallback) ──────────────────────────
try:
    import cairosvg
    cairosvg.svg2png(url=str(svg_path), write_to=str(OUT_FILE), scale=2.0)
    print(f"PNG saved → {OUT_FILE}")
except ImportError:
    try:
        from PIL import Image
        import subprocess, sys
        result = subprocess.run(
            ["inkscape", "--export-type=png", f"--export-filename={OUT_FILE}",
             "--export-dpi=150", str(svg_path)],
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"PNG saved via inkscape → {OUT_FILE}")
        else:
            print(f"inkscape failed: {result.stderr.decode()}")
            print("请手动将 SVG 转换为 PNG：" + str(svg_path))
    except Exception as e:
        print(f"PNG 转换失败，请手动转换 SVG: {e}\n{svg_path}")
