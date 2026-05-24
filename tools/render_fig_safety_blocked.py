"""
生成图 5-2：危险命令拦截与高风险确认界面（fig:safety-blocked）
展示两种情形：
  A. blocked 命令 —— rm -rf / 被直接拦截
  B. high 风险命令 —— chmod -R 777 /home/user 要求二次确认后取消
"""
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

OUT_DIR = Path(__file__).resolve().parent.parent / "thesis" / "template" / "pic"
OUT_FILE = OUT_DIR / "fig_safety_blocked.png"

os.makedirs(OUT_DIR, exist_ok=True)

console = Console(record=True, width=88)

# ── 场景 A：blocked（直接拦截） ─────────────────────────────────────
console.rule("[dim]场景 A  |  blocked 命令[/dim]")
console.print()
console.print("[bold]> [/bold]删除根目录下所有内容\n")

console.print(
    Panel(
        "rm -rf /",
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)

console.print(
    Panel(
        "[red]该命令匹配黑名单规则 rm -rf /，将递归删除整个根文件系统，操作不可逆。[/red]\n\n"
        "如需执行高权限操作，请联系管理员申请权限。",
        title="命令已拦截",
        border_style="red",
    )
)
console.print(Rule(style="dim"))

# ── 场景 B：high 风险，用户主动取消 ──────────────────────────────────
console.print()
console.rule("[dim]场景 B  |  high 风险命令[/dim]")
console.print()
console.print("[bold]> [/bold]把 /home/user/project 目录权限改为 777\n")

console.print(
    Panel(
        "chmod -R 777 /home/user/project",
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)

console.print(
    Panel(
        "[yellow]高风险命令[/yellow]\n"
        "影响范围：递归修改 /home/user/project 及其所有子目录/文件的权限位。\n"
        "将使任意用户均可读写执行该目录下的所有文件，可能导致安全漏洞。",
        title="风险警告",
        border_style="yellow",
    )
)
console.print("[bold]该命令风险较高，确认继续? [/bold][dim]\\[y/n][/dim] [red]n[/red]")
console.print()
console.print("[yellow]已取消执行。[/yellow]")
console.print(Rule(style="dim"))

svg_path = OUT_DIR / "fig_safety_blocked.svg"
console.save_svg(str(svg_path), title="Shell Agent CLI - 安全拦截")
print(f"SVG saved → {svg_path}")

try:
    import cairosvg
    cairosvg.svg2png(url=str(svg_path), write_to=str(OUT_FILE), scale=2.0)
    print(f"PNG saved → {OUT_FILE}")
except ImportError:
    try:
        import subprocess
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
