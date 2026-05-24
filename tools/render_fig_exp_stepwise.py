"""
生成图 6-2：多步任务分步执行实验实拍（fig:exp-stepwise-case）
展示任务：压缩日志目录 → 移至备份服务器 → 清理旧文件（三步循环）
"""
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule

OUT_DIR = Path(__file__).resolve().parent.parent / "thesis" / "template" / "pic"
OUT_FILE = OUT_DIR / "fig_exp_stepwise_case.png"

os.makedirs(OUT_DIR, exist_ok=True)

console = Console(record=True, width=88)

# ── 任务描述 ──────────────────────────────────────────────────────────
console.print(
    Panel.fit(
        "[bold cyan]分步任务[/bold cyan]\n"
        "压缩 /var/log/myapp 日志目录，移至 /backup/，并删除7天前的旧备份包",
        border_style="cyan",
    )
)
console.print()

# ── 步骤 1 ────────────────────────────────────────────────────────────
console.print("[magenta]步骤 1[/magenta]")
console.print(
    Panel(
        Syntax(
            "tar -czf /tmp/myapp-logs.tar.gz /var/log/myapp",
            "bash", theme="monokai", line_numbers=False,
        ),
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)
console.print(
    Panel(
        "[dim]（dry-run）将以只读方式打包 /var/log/myapp，写入 /tmp/myapp-logs.tar.gz。[/dim]",
        title="执行预览（模拟）",
        border_style="blue",
    )
)
console.print("[bold]执行该步骤命令? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print("[green]步骤 1 执行完毕，返回码 0[/green]")
console.print("[bold]继续下一步? [/bold][dim]\\[y/n][/dim] [green]y[/green]\n")

# ── 步骤 2 ────────────────────────────────────────────────────────────
console.print("[magenta]步骤 2[/magenta]")
console.print(
    Panel(
        Syntax(
            "mv /tmp/myapp-logs.tar.gz /backup/",
            "bash", theme="monokai", line_numbers=False,
        ),
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)
console.print(
    Panel(
        "[dim]（dry-run）将 /tmp/myapp-logs.tar.gz 移动至 /backup/ 目录，原路径文件将消失。[/dim]",
        title="执行预览（模拟）",
        border_style="blue",
    )
)
console.print("[bold]执行该步骤命令? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print("[green]步骤 2 执行完毕，返回码 0[/green]")
console.print("[bold]继续下一步? [/bold][dim]\\[y/n][/dim] [green]y[/green]\n")

# ── 步骤 3 ────────────────────────────────────────────────────────────
console.print("[magenta]步骤 3[/magenta]")
console.print(
    Panel(
        Syntax(
            'find /backup -name "myapp-logs*.tar.gz" -mtime +7 -delete',
            "bash", theme="monokai", line_numbers=False,
        ),
        title="[bold cyan]生成命令[/bold cyan]",
        border_style="cyan",
    )
)
console.print(
    Panel(
        "[yellow]高风险命令[/yellow]\n"
        "影响范围：删除 /backup 下所有超过7天的 myapp-logs*.tar.gz 文件，不可撤销。",
        title="风险警告",
        border_style="yellow",
    )
)
console.print("[bold]该命令风险较高，确认继续? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print(
    Panel(
        "[dim]（dry-run）将匹配 /backup/myapp-logs-20250428.tar.gz 等文件并删除。[/dim]",
        title="执行预览（模拟）",
        border_style="blue",
    )
)
console.print("[bold]执行该步骤命令? [/bold][dim]\\[y/n][/dim] [green]y[/green]")
console.print("[green]步骤 3 执行完毕，返回码 0[/green]")
console.print("[bold]继续下一步? [/bold][dim]\\[y/n][/dim] [green]y[/green]\n")

# ── 任务完成 ──────────────────────────────────────────────────────────
console.print("[green]分步任务已完成或无需继续执行。[/green]")
console.print(Rule(style="dim"))

svg_path = OUT_DIR / "fig_exp_stepwise_case.svg"
console.save_svg(str(svg_path), title="Shell Agent CLI - 分步执行")
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
