import sys
import os
import json
import re
import argparse
import uuid
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from .shell_agent_client import QwenHTTP
except ImportError:
    from shell_agent_client import QwenHTTP

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.syntax import Syntax

from config.shell_config import get_shell_syntax

try:
    from .command_safety import classify_command, validate_syntax, simulate_command
except ImportError:
    from command_safety import classify_command, validate_syntax, simulate_command

try:
    from .execution_logger import ExecutionLogger
except ImportError:
    from execution_logger import ExecutionLogger


class ShellAgentCLI:

    def __init__(self, target_shell: str = "bash"):
        self.console = Console()
        self._custom_session_consumed = False
        self._stepwise_max_steps = 12
        self.chats = []
        self._chat_counter = 0
        self.active_chat_index = 0
        self._chat_store_path = self._resolve_chat_store_path()
        self._load_chat_state()
        if not self.chats:
            self._create_chat(title="对话 1", switch_to=True)
            self._save_chat_state()
        self.target_shell = get_shell_syntax(target_shell).name
        self._working_memory = self._init_working_memory()
        self._exec_logger = ExecutionLogger()
        self.setup_components()

    def _init_working_memory(self) -> Dict[str, Any]:
        return {
            "last_command": "",
            "last_output": "",
            "items": [],
        }

    def _resolve_chat_store_path(self) -> Path:
        custom = os.getenv("SHELL_AGENT_CHAT_STORE", "").strip()
        if custom:
            return Path(custom).resolve()
        return (Path(__file__).resolve().parent.parent / "data" / "cli_chats.json").resolve()

    def _save_chat_state(self) -> None:
        payload = {
            "active_chat_index": self.active_chat_index,
            "chat_counter": self._chat_counter,
            "chats": self.chats,
        }
        self._chat_store_path.parent.mkdir(parents=True, exist_ok=True)
        self._chat_store_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_chat_state(self) -> None:
        if not self._chat_store_path.exists():
            return

        try:
            payload = json.loads(self._chat_store_path.read_text(encoding="utf-8"))
        except Exception:
            return

        chats = payload.get("chats")
        if not isinstance(chats, list):
            return

        normalized = []
        for chat in chats:
            if not isinstance(chat, dict):
                continue
            title = str(chat.get("title", "")).strip()
            session_id = str(chat.get("session_id", "")).strip()
            if not session_id:
                continue
            normalized.append({
                "title": title or "对话",
                "session_id": session_id,
            })

        if not normalized:
            return

        self.chats = normalized
        self._chat_counter = max(int(payload.get("chat_counter", len(self.chats))), len(self.chats))
        idx = int(payload.get("active_chat_index", 0)) if isinstance(payload.get("active_chat_index", 0), int) else 0
        if idx < 0 or idx >= len(self.chats):
            idx = 0
        self._set_active_chat(idx, save=False)

    def _build_session_id(self) -> str:
        """Build a unique session id for each CLI process unless explicitly overridden."""
        custom = os.getenv("SHELL_AGENT_SESSION_ID", "").strip()
        if custom and not self._custom_session_consumed:
            self._custom_session_consumed = True
            return custom
        return f"cli_{os.getpid()}_{uuid.uuid4().hex[:8]}"

    def _set_active_chat(self, index: int, save: bool = True) -> None:
        self.active_chat_index = index
        self.session_id = self.chats[index]["session_id"]
        if save:
            self._save_chat_state()

    def _create_chat(self, title: str = "", switch_to: bool = True) -> dict:
        self._chat_counter += 1
        chat = {
            "title": title.strip() or f"对话 {self._chat_counter}",
            "session_id": self._build_session_id(),
        }
        self.chats.append(chat)
        self._save_chat_state()
        if switch_to:
            self._set_active_chat(len(self.chats) - 1)
        return chat

    def _switch_chat(self, selector: str) -> bool:
        s = selector.strip()
        if not s:
            return False

        if s.isdigit():
            idx = int(s) - 1
            if 0 <= idx < len(self.chats):
                self._set_active_chat(idx)
                return True

        for idx, chat in enumerate(self.chats):
            if chat["session_id"] == s or chat["title"] == s:
                self._set_active_chat(idx)
                return True

        return False

    def setup_components(self):

        self.console.print(
            Panel.fit(
                "[bold cyan]Shell Agent CLI[/bold cyan]\n"
                "基于大语言模型的命令行助手，支持自然语言输入，生成Shell命令并提供说明。\n",
                border_style="cyan"
            )
        )

        self.console.print(
            "[dim]new新建对话 | chats会话列表 | use切换对话 | session查看会话 | memory查看记忆 | clear清空记忆 | exit退出[/dim]\n"
        )
        self.console.print(f"[dim]目标 Shell: {self.target_shell}[/dim]\n")
        self.console.print(f"[dim]当前会话: {self.chats[self.active_chat_index]['title']} ({self.session_id})[/dim]\n")

        # Client for backend model server
        self.llm = QwenHTTP()

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
                # json.loads correctly handles \uXXXX and other JSON escape sequences
                # without corrupting multi-byte (e.g. Chinese) characters.
                return json.loads(f'"{raw}"')
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

        # Avoid silent UI output when model returns an empty object like {}.
        if not command and not explanation and not warning:
            warning = "模型回复为空，未返回可执行命令或说明"
            explanation = "请重试一次；如果问题持续，请检查模型服务状态。"

        return {
            "command": command,
            "explanation": explanation,
            "warning": warning,
        }

    def parse_response(self, response: str) -> dict:
        response = response.strip()
        # 移除 Markdown 代码块围栏
        response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response, flags=re.IGNORECASE | re.DOTALL).strip()

        if not response:
            return {
                "command": "",
                "explanation": "请重试一次；如果问题持续，请检查模型服务状态。",
                "warning": "模型回复为空，未返回可执行命令或说明",
            }

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

    def _run_security_checks(self, command: str) -> bool:
        """三步预执行安全校验。返回 True 表示允许继续执行，False 表示已中止。"""
        # 步骤 1：语法校验
        ok, err = validate_syntax(command, shell=self.target_shell)
        if not ok:
            self.console.print(
                Panel(f"[red]语法错误，无法执行：[/red]\n{err}", title="语法检查", border_style="red")
            )
            return False

        # 步骤 2：风险分级
        result = classify_command(command, shell=self.target_shell)
        if result.risk_level == "blocked":
            self.console.print(
                Panel(
                    f"[red]{result.reason}[/red]\n\n如需执行高权限操作，请联系管理员申请权限。",
                    title="命令已拦截",
                    border_style="red",
                )
            )
            self._exec_logger.log(
                natural_language="",
                command=command,
                risk_level="blocked",
                returncode=None,
                elapsed_sec=0.0,
                session_id=self.session_id,
            )
            return False

        if result.risk_level == "high":
            self.console.print(
                Panel(
                    f"[yellow]高风险命令[/yellow]\n{result.scope_description}\n{result.reason}",
                    title="风险警告",
                    border_style="yellow",
                )
            )
            if not Confirm.ask("该命令风险较高，确认继续?"):
                return False

        # 步骤 3：效果模拟预览
        preview = simulate_command(command, shell=self.target_shell)
        if preview:
            self.console.print(
                Panel(preview, title="执行预览（模拟）", border_style="blue")
            )
        return True

    def adapt_command_for_shell(self, command: str) -> str:
        """Adapt command syntax for the selected shell with common Bash/Zsh differences."""
        cmd = command.strip()
        if not cmd:
            return cmd

        if self.target_shell == "zsh":
            # Bash indirect expansion: ${!var} -> ${(P)var}
            cmd = re.sub(r'\$\{!([A-Za-z_][A-Za-z0-9_]*)\}', r'${(P)\1}', cmd)
            # Bash array length: ${#arr[@]} -> ${#arr}
            cmd = re.sub(r'\$\{#([A-Za-z_][A-Za-z0-9_]*)\[@\]\}', r'${#\1}', cmd)
            # Convert common explicit 0-based indices to zsh's 1-based indices.
            cmd = self._shift_array_indices(cmd, delta=1)
            return cmd

        if self.target_shell == "bash":
            # Zsh indirect expansion: ${(P)var} -> ${!var}
            cmd = re.sub(r'\$\{\(P\)([A-Za-z_][A-Za-z0-9_]*)\}', r'${!\1}', cmd)
            # Zsh array length: ${#arr} -> ${#arr[@]}
            cmd = re.sub(r'\$\{#([A-Za-z_][A-Za-z0-9_]*)\}', r'${#\1[@]}', cmd)
            # Convert common explicit 1-based indices back to bash's 0-based indices.
            cmd = self._shift_array_indices(cmd, delta=-1)
            return cmd

        return cmd

    def _shift_array_indices(self, command: str, delta: int) -> str:
        """Shift explicit array numeric indices in common patterns."""
        def _convert(match):
            name = match.group(1)
            idx = int(match.group(2)) + delta
            if idx < 0:
                idx = 0
            return f"${{{name}[{idx}]}}"

        return re.sub(
            r'\$\{([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]\}',
            _convert,
            command,
        )

    def _build_stepwise_prompt(self, task: str, step_index: int) -> str:
        """Build a constrained prompt asking the model for only the next step."""
        return (
            "你正在执行分步命令生成模式。"
            f"总任务目标：{task}\n"
            f"请只返回第 {step_index} 步，不要返回后续步骤。"
            "如果任务已经完成，请返回 command 为空字符串，并在 explanation 写明已完成。"
            "命令应尽量单步、可执行、低风险，并符合当前目标 shell。"
        )

    def _should_run_stepwise(self, user_input: str) -> bool:
        """Decide whether the request needs multi-step execution using keyword heuristics."""
        text = user_input.strip().lower()
        if not text:
            return False

        # Multi-stage connectors and sequencing hints.
        connectors = ["然后", "再", "最后", "首先", "接着", "并且", "after that", "then", "next", "finally"]
        complex_keywords = ["部署", "迁移", "安装", "配置", "排查", "诊断", "搭建", "上线", "流水线", "install", "configure", "deploy", "migrate", "setup"]

        connector_hit = any(k in text for k in connectors)
        keyword_hits = sum(1 for k in complex_keywords if k in text)
        long_request = len(text) >= 36
        return connector_hit or keyword_hits >= 2 or (keyword_hits >= 1 and long_request)

    def _run_stepwise_task(self, task: str) -> None:
        """Generate and optionally execute one command per step with user confirmation."""
        if not task.strip():
            self.console.print("[yellow]任务为空，无法进行分步执行[/yellow]")
            return

        self.console.print(Panel.fit(f"[bold cyan]分步任务[/bold cyan]\n{task}", border_style="cyan"))

        for step_index in range(1, self._stepwise_max_steps + 1):
            prompt = self._build_stepwise_prompt(task, step_index)

            with self.console.status(f"[bold yellow]AI 正在生成第 {step_index} 步..."):
                response = self.llm.generate_command(
                    user_input=prompt,
                    session_id=self.session_id,
                    target_shell=self.target_shell,
                )

            parsed = self.parse_response(response)
            if parsed["command"]:
                parsed["command"] = self.adapt_command_for_shell(parsed["command"])

            self.console.print(f"[magenta]步骤 {step_index}[/magenta]")
            self.render_result(parsed)

            if not parsed["command"]:
                self.console.print("[green]分步任务已完成或无需继续执行。[/green]")
                self.console.print(Rule(style="dim"))
                return

            if not self._run_security_checks(parsed["command"]):
                self.console.print("[red]安全检查未通过，分步任务终止。[/red]")
                self.console.print(Rule(style="dim"))
                return

            if Confirm.ask("执行该步骤命令?"):
                _, output_text = self._execute_command(parsed["command"], natural_language=task)
                self._update_working_memory(parsed["command"], output_text)
            else:
                self.console.print("[yellow]已取消当前步骤执行，分步任务终止。[/yellow]")
                self.console.print(Rule(style="dim"))
                return

            if not Confirm.ask("继续下一步?"):
                self.console.print("[yellow]分步任务已暂停。可直接继续输入后续目标。[/yellow]")
                self.console.print(Rule(style="dim"))
                return

        self.console.print("[yellow]已达到分步上限，任务自动暂停。[/yellow]")
        self.console.print(Rule(style="dim"))

    def _extract_items_from_output(self, output_text: str, max_items: int = 10) -> List[str]:
        items = []
        for line in output_text.splitlines():
            value = line.strip()
            if not value:
                continue
            if value.startswith(("total ", "权限拒绝", "permission denied", "find:", "ls:")):
                continue
            items.append(value)
            if len(items) >= max_items:
                break
        return items

    def _update_working_memory(self, command: str, output_text: str) -> None:
        items = self._extract_items_from_output(output_text)
        self._working_memory = {
            "last_command": command.strip(),
            "last_output": output_text.strip()[:1200],
            "items": items,
        }

    def _contains_referential_request(self, user_input: str) -> bool:
        text = user_input.lower()
        zh_markers = ["这些", "那些", "它们", "上述", "上一步", "上一个结果", "刚才的结果"]
        en_markers = ["these", "those", "them", "previous result", "last result", "above result", "it"]
        return any(k in text for k in zh_markers + en_markers)

    def _prepare_model_input(self, user_input: str) -> Tuple[str, Optional[Dict[str, str]]]:
        memory = getattr(self, "_working_memory", None) or self._init_working_memory()
        has_items = bool(memory.get("items"))

        if self._contains_referential_request(user_input) and not has_items:
            return "", {
                "command": "",
                "explanation": "缺少可引用的上一步结果，请先执行一次查询（例如 find/ls），再使用代词继续操作。",
                "warning": "未检测到可用于指代消解的实体记忆",
            }

        if not has_items and not memory.get("last_command"):
            return user_input, None

        items = memory.get("items", [])
        memory_block = (
            "[WORKING_MEMORY]\n"
            f"last_command: {memory.get('last_command', '')}\n"
            f"items: {json.dumps(items, ensure_ascii=False)}\n"
            f"last_output_preview: {memory.get('last_output', '')[:400]}\n"
            "[/WORKING_MEMORY]\n"
        )
        return f"{memory_block}\nUser request:\n{user_input}", None

    def _generate_from_user_input(self, user_input: str) -> Dict[str, str]:
        effective_input, early_result = self._prepare_model_input(user_input)
        if early_result is not None:
            return early_result

        response = self.llm.generate_command(
            user_input=effective_input,
            session_id=self.session_id,
            target_shell=self.target_shell,
        )
        parsed = self.parse_response(response)
        if parsed["command"]:
            parsed["command"] = self.adapt_command_for_shell(parsed["command"])
        return parsed

    def _execute_command(self, command: str, natural_language: str = "") -> Tuple[int, str]:
        import time
        t0 = time.monotonic()
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        elapsed = time.monotonic() - t0
        output_text = (result.stdout or "") + (result.stderr or "")

        if result.stdout:
            self.console.print(result.stdout.rstrip())
        if result.stderr:
            self.console.print(f"[red]{result.stderr.rstrip()}[/red]")

        safety_result = classify_command(command, shell=self.target_shell)
        self._exec_logger.log(
            natural_language=natural_language,
            command=command,
            risk_level=safety_result.risk_level,
            returncode=result.returncode,
            elapsed_sec=elapsed,
            session_id=self.session_id,
        )
        return result.returncode, output_text

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

    def render_memory_context(self, payload: dict):
        summary = (payload.get("summary") or "").strip()
        recent_messages = payload.get("recent_messages") or []
        relevant = (payload.get("relevant_memory") or "").strip()

        table = Table(show_header=False, box=None)
        table.add_row("[cyan]会话 ID[/cyan]", str(payload.get("session_id", self.session_id)))
        table.add_row("[cyan]摘要[/cyan]", summary or "(空)")

        if recent_messages:
            recent_text = "\n".join(
                [f"[{msg.get('role', 'unknown')}] {msg.get('content', '')}" for msg in recent_messages]
            )
            table.add_row("[cyan]最近对话[/cyan]", recent_text)
        else:
            table.add_row("[cyan]最近对话[/cyan]", "(空)")

        if relevant:
            table.add_row("[cyan]相关记忆[/cyan]", relevant)

        self.console.print(
            Panel(
                table,
                title="当前模型记忆",
                border_style="magenta"
            )
        )

    def render_chat_list(self):
        table = Table(title="会话列表")
        table.add_column("#", style="cyan", no_wrap=True)
        table.add_column("标题", style="white")
        table.add_column("Session ID", style="dim")
        table.add_column("当前", style="green", no_wrap=True)

        for idx, chat in enumerate(self.chats):
            is_current = "*" if idx == self.active_chat_index else ""
            table.add_row(str(idx + 1), chat["title"], chat["session_id"], is_current)

        self.console.print(table)

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
                    self.console.print("[yellow]程序运行结束[/yellow]")
                    break

                if user_input.lower() == "chats":
                    self.render_chat_list()
                    continue

                if user_input.lower().startswith("new"):
                    title = user_input[3:].strip()
                    chat = self._create_chat(title=title, switch_to=True)
                    self.console.print(
                        f"[green]已切换到新会话[/green] [cyan]{chat['title']}[/cyan] ({chat['session_id']})"
                    )
                    continue

                if user_input.lower().startswith("use"):
                    selector = user_input[3:].strip()
                    if not selector:
                        self.console.print("[yellow]用法: use <序号|标题|session_id>[/yellow]")
                        continue
                    switched = self._switch_chat(selector)
                    if switched:
                        current = self.chats[self.active_chat_index]
                        self.console.print(
                            f"[green]已切换到会话[/green] [cyan]{current['title']}[/cyan] ({current['session_id']})"
                        )
                    else:
                        self.console.print("[red]未找到指定会话[/red]")
                    continue

                if user_input.lower() == "clear":
                    try:
                        cleared = self.llm.clear_memory(self.session_id)
                        if cleared:
                            self.console.print("[yellow]记忆已清除[/yellow]")
                        else:
                            self.console.print("[red]清除记忆失败[/red]")
                    except Exception as clear_exc:
                        self.console.print(f"[red]清除记忆失败: {clear_exc}[/red]")
                    continue

                if user_input.lower() == "session":
                    current = self.chats[self.active_chat_index]
                    self.console.print(
                        f"[cyan]当前会话: {current['title']} | ID: {self.session_id} | 序号: {self.active_chat_index + 1}[/cyan]"
                    )
                    continue

                if user_input.lower().startswith("exportlog"):
                    path = user_input[9:].strip() or "data/execution_export.csv"
                    count = self._exec_logger.export_csv(Path(path))
                    self.console.print(f"[green]已导出 {count} 条日志到 {path}[/green]")
                    continue

                if user_input.lower().startswith("exportlog"):
                    path = user_input[9:].strip() or "data/execution_export.csv"
                    count = self._exec_logger.export_csv(Path(path))
                    self.console.print(f"[green]已导出 {count} 条日志到 {path}[/green]")
                    continue

                if user_input.lower() == "memory":
                    try:
                        payload = self.llm.get_memory_context(self.session_id)
                        self.render_memory_context(payload)
                    except Exception as mem_exc:
                        self.console.print(f"[red]读取记忆失败: {mem_exc}[/red]")
                    continue

                # LLM 推理（分步决策与普通推理都在 spinner 内执行）
                with self.console.status("[bold yellow]AI 正在思考..."):
                    is_stepwise = self._should_run_stepwise(user_input)
                    if not is_stepwise:
                        parsed = self._generate_from_user_input(user_input)

                if is_stepwise:
                    self._run_stepwise_task(user_input)
                    continue

                self.render_result(parsed)

                # 安全检查
                if parsed["command"]:
                    if self._run_security_checks(parsed["command"]):
                        if Confirm.ask("执行该命令?"):
                            _, output_text = self._execute_command(parsed["command"], natural_language=user_input)
                            self._update_working_memory(parsed["command"], output_text)

                self.console.print(Rule(style="dim"))

            except KeyboardInterrupt:
                self.console.print("\n[yellow]程序运行结束[/yellow]")
                break

            except Exception as e:
                self.console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shell Agent CLI")
    parser.add_argument(
        "--shell",
        default="bash",
        choices=["bash", "zsh"],
        help="target shell syntax for generated commands",
    )
    args = parser.parse_args()

    cli = ShellAgentCLI(target_shell=args.shell)

    cli.run()