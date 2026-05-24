"""SVG → PNG using html2image (headless browser)"""
from html2image import Html2Image
from pathlib import Path

pic = Path("thesis/template/pic")
hti = Html2Image(output_path=str(pic))

import re

# CJK-compatible font stack for Windows
CJK_FONT = "Consolas, 'Microsoft YaHei Mono', 'Microsoft YaHei', SimHei, monospace"

def patch_svg_font(svg: str) -> str:
    """Replace Fira Code font references in the SVG with a CJK-capable stack."""
    # Replace font-family in style attributes and CSS blocks
    svg = svg.replace("Fira Code", CJK_FONT)
    svg = svg.replace("'Fira Code'", CJK_FONT)
    svg = svg.replace('"Fira Code"', CJK_FONT)
    return svg

configs = [
    ("fig_cli_runtime",       1100, 970),
    ("fig_safety_blocked",    1100, 850),
    ("fig_exp_stepwise_case", 1100, 1650),
]

for name, w, h in configs:
    svg_path = pic / f"{name}.svg"
    svg_content = patch_svg_font(svg_path.read_text(encoding="utf-8"))
    html = (
        "<html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;background:#1e1e1e'>"
        + svg_content
        + "</body></html>"
    )
    hti.size = (w, h)
    hti.screenshot(html_str=html, save_as=f"{name}.png")
    print(f"OK: {name}.png")
