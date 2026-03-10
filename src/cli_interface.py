import sys
import os
import json
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory.sqlite_memory import SQLiteMemory

try:
    from .shell_agent_client import SQLiteMemoryWrapper, QwenHTTP
except ImportError:
    from shell_agent_client import SQLiteMemoryWrapper, QwenHTTP

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.syntax import Syntax


class ShellAgentCLI:

    def __init__(self):
        self.console = Console()
        self.session_id = "cli_session"
        self.setup_components()

    def setup_components(self):

        self.console.print(
            Panel.fit(
                "[bold cyan]Shell Agent CLI[/bold cyan]\n"
                "自然语言 → Shell 命令",
                border_style="cyan"
            )
        )

        self.console.print(
            "[dim]输入自然语言生成命令 | exit退出 | clear清空记忆[/dim]\n"
        )

        # LLM
        self.llm = QwenHTTP()

        # Memory
        db_path = os.path.join(
            os.path.dirname(__file__), "../data/cli_memory.db"
        )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        sqlite_mem = SQLiteMemory(
            db_path=db_path,
            session_id=self.session_id
        )

        self.memory = SQLiteMemoryWrapper(sqlite_mem)

        # Prompt
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "../prompts/shell_assistant.prompt"
        )

        prompt_text = Path(prompt_path).read_text(encoding="utf-8")

        self.prompt = PromptTemplate(
            input_variables=[
                "summary",
                "recent_history",
                "relevant_memory",
                "input"
            ],
            template=prompt_text
        )

        # Chain
        self.chain = (
            RunnablePassthrough.assign(
                summary=lambda x: self.memory.load_memory_variables(x)["summary"],
                recent_history=lambda x: self.memory.load_memory_variables(x)["recent_history"],
                relevant_memory=lambda x: self.memory.load_memory_variables(x)["relevant_memory"]
            )
            | self.prompt
            | self.llm
        )

        self.console.print("[green]初始化完成[/green]\n")

    # ----------------------------
    # 响应解析
    # ----------------------------

    def _extract_first_json_object(self, text: str):
        """Extract the first JSON object from text using a tolerant decoder scan."""
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                obj, _ = decoder.raw_decode(text[idx:])
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
        return None

    def _repair_common_json_issues(self, text: str) -> str:
        """Repair common malformed JSON patterns from LLM outputs."""
        # Replace illegal escape sequences (e.g. \*) with escaped backslash (\\*).
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

    def _extract_json_fields_fallback(self, text: str) -> dict:
        """Fallback field extraction when full JSON parsing fails."""
        def _find(key: str) -> str:
            pattern = rf'"{key}"\s*:\s*"((?:\\.|[^"\\])*)"'
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                return ""
            raw = match.group(1)
            try:
                return bytes(raw, "utf-8").decode("unicode_escape").strip()
            except Exception:
                return raw.replace('\\"', '"').replace('\\\\', '\\').strip()

        return {
            "command": _find("command"),
            "explanation": _find("explanation"),
            "warning": _find("warning")
        }

    def _extract_labeled_fields_fallback(self, text: str) -> dict:
        """Parse non-JSON labeled output like '命令: ...\n说明: ...\n警告: ...'."""
        normalized = text.replace("\r\n", "\n")

        def _from_pattern(pattern: str) -> str:
            match = re.search(pattern, normalized, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip() if match else ""

        command = _from_pattern(r'(?:^|\n)\s*(?:命令|command)\s*[：:]\s*(.+?)(?=\n\s*(?:说明|explanation|警告|warning)\s*[：:]|\Z)')
        explanation = _from_pattern(r'(?:^|\n)\s*(?:说明|explanation)\s*[：:]\s*(.+?)(?=\n\s*(?:命令|command|警告|warning)\s*[：:]|\Z)')
        warning = _from_pattern(r'(?:^|\n)\s*(?:警告|warning)\s*[：:]\s*(.+?)(?=\n\s*(?:命令|command|说明|explanation)\s*[：:]|\Z)')

        return {
            "command": command,
            "explanation": explanation,
            "warning": warning,
        }

    def _looks_like_shell_command(self, command: str) -> bool:
        """Heuristic check to distinguish shell commands from natural language."""
        cmd = command.strip()
        if not cmd:
            return False

        # Obvious natural-language markers.
        if any(ch in cmd for ch in ["\n", "。", "，"]):
            return False
        if cmd.startswith(("说明", "解释", "答复", "回应")):
            return False

        # Common shell command prefixes and operators.
        command_prefixes = [
            "ls", "cd", "pwd", "find", "grep", "cat", "echo", "mkdir", "rm", "cp", "mv",
            "chmod", "chown", "ps", "kill", "top", "df", "du", "tar", "gzip", "ssh", "scp",
            "curl", "wget", "python", "pip", "conda", "git", "apt", "yum", "dnf", "systemctl",
            "docker", "kubectl", "crontab", "nohup", "sed", "awk", "sort", "head", "tail"
        ]
        if any(cmd == prefix or cmd.startswith(prefix + " ") for prefix in command_prefixes):
            return True

        shell_signals = ["|", "&&", "||", ">", "<", "$(", "./", "~/", "--"]
        if any(signal in cmd for signal in shell_signals):
            return True

        # Final lightweight shape check for command-like tokens.
        return bool(re.match(r'^[A-Za-z0-9_./-]+(?:\s+.+)?$', cmd))

    def _normalize_parsed_result(self, parsed: dict) -> dict:
        """Normalize parsed fields to reduce false command extraction."""
        command = parsed.get("command", "").strip()
        explanation = parsed.get("explanation", "").strip()
        warning = parsed.get("warning", "").strip()

        parser_warnings = {
            "模型回复格式部分异常，已尝试容错解析",
            "模型回复非JSON，已按标签容错解析",
        }

        if command and not self._looks_like_shell_command(command):
            if not explanation:
                explanation = command
            command = ""

        # If this is a normal conversational reply with no command, suppress parser-internal warning.
        if not command and explanation and warning in parser_warnings:
            warning = ""

        return {
            "command": command,
            "explanation": explanation,
            "warning": warning,
        }

    def parse_response(self, response: str) -> dict:
        response = response.strip()
        # 移除 Markdown 代码块围栏
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response, flags=re.IGNORECASE | re.DOTALL).strip()

        parsed = self._extract_first_json_object(response)
        if parsed is None:
            repaired = self._repair_common_json_issues(response)
            parsed = self._extract_first_json_object(repaired)

        if isinstance(parsed, dict):
            command = str(parsed.get("command", "")).strip()
            # LLM output may contain escaped wildcards from malformed JSON (e.g. /\*).
            command = command.replace('\\*', '*').replace('\\?', '?')
            return self._normalize_parsed_result({
                "command": command,
                "explanation": str(parsed.get("explanation", "")).strip(),
                "warning": str(parsed.get("warning", "")).strip()
            })

        # 字段级兜底：即使JSON整体非法，也尽量提取关键字段
        fallback = self._extract_json_fields_fallback(response)
        if fallback["command"] or fallback["explanation"] or fallback["warning"]:
            if not fallback["warning"]:
                fallback["warning"] = "模型回复格式部分异常，已尝试容错解析"
            return self._normalize_parsed_result(fallback)

        labeled = self._extract_labeled_fields_fallback(response)
        if labeled["command"] or labeled["explanation"] or labeled["warning"]:
            if not labeled["warning"]:
                labeled["warning"] = "模型回复非JSON，已按标签容错解析"
            return self._normalize_parsed_result(labeled)

        return {
            "command": "",
            "explanation": response,
            "warning": "模型回复格式非法，未能识别 JSON"
        }
        # ----------------------------
        # 命令安全检查
        # ----------------------------

    def check_command_safety(self, command):

        dangerous = [
            "rm -rf /",
            "mkfs",
            "dd if=",
            ":(){:|:&};:",
            "shutdown",
            "reboot"
        ]

        for d in dangerous:
            if d in command:
                return False

        return True

    # ----------------------------
    # 输出UI
    # ----------------------------

    def render_result(self, parsed):

        if parsed["command"]:

            syntax = Syntax(
                parsed["command"],
                "bash",
                theme="monokai",
                line_numbers=False
            )

            self.console.print(
                Panel(
                    syntax,
                    title="[bold]Shell Command[/bold]",
                    border_style="green"
                )
            )

        table = Table(show_header=False, box=None)

        if parsed["explanation"]:
            table.add_row(
                "[cyan]说明[/cyan]",
                parsed["explanation"]
            )

        if parsed["warning"]:
            table.add_row(
                "[red]警告[/red]",
                parsed["warning"]
            )

        if len(table.rows) > 0:
            self.console.print(
                Panel(
                    table,
                    title="生成结果",
                    border_style="blue"
                )
            )

    # ----------------------------
    # 主循环
    # ----------------------------

    def run(self):

        while True:

            try:

                user_input = Prompt.ask("[bold green]您[/bold green]")

                if not user_input.strip():
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    self.console.print("[yellow]再见[/yellow]")
                    break

                if user_input.lower() == "clear":
                    self.memory.clear()
                    self.console.print("[yellow]记忆已清除[/yellow]")
                    continue

                # LLM 推理
                with self.console.status("[bold yellow]AI 正在思考..."):
                    response = self.chain.invoke({"input": user_input})

                parsed = self.parse_response(response)

                self.render_result(parsed)

                # 安全检查
                if parsed["command"]:

                    safe = self.check_command_safety(parsed["command"])

                    if not safe:
                        self.console.print(
                            "[red]危险命令，已阻止执行[/red]"
                        )
                    else:

                        if Confirm.ask("执行该命令?"):
                            os.system(parsed["command"])

                # 保存 memory
                self.memory.save_context(
                    {"input": user_input},
                    {
                        "output": f"命令: {parsed['command']}\n说明: {parsed['explanation']}"
                    }
                )

                self.console.print(Rule(style="dim"))

            except KeyboardInterrupt:
                self.console.print("\n[yellow]再见[/yellow]")
                break

            except Exception as e:
                self.console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":

    cli = ShellAgentCLI()

    cli.run()