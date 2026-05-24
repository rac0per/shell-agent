from pathlib import Path
import re
svg = Path("thesis/template/pic/fig_cli_runtime.svg").read_text(encoding="utf-8")
fonts = re.findall(r"font-family[:\s=]+[\"']?([^\"';,<>\n]+)", svg)
print(set(fonts[:30]))
