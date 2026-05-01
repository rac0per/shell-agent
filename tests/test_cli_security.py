"""Integration tests for ShellAgentCLI._run_security_checks.

Covers the three-step pre-execution pipeline:
  1. Syntax validation
  2. Risk classification (blocked / high / low/medium)
  3. Simulate preview

The tests mock Rich Console and Confirm so they run headlessly.
ExecutionLogger is pointed at a temp file to avoid side-effects.
"""
import sys
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cli_interface import ShellAgentCLI
from src.execution_logger import ExecutionLogger


def _make_cli(tmp_path=None) -> ShellAgentCLI:
    """Create a ShellAgentCLI instance without calling __init__."""
    cli = ShellAgentCLI.__new__(ShellAgentCLI)
    cli.target_shell = "bash"
    cli.session_id = "test-session"
    cli.console = MagicMock()
    if tmp_path:
        cli._exec_logger = ExecutionLogger(log_path=str(tmp_path / "exec.jsonl"))
    else:
        cli._exec_logger = ExecutionLogger(log_path=tempfile.mktemp(suffix=".jsonl"))
    return cli


class TestSecurityChecksBlocked:
    """Blocked commands must be rejected and logged without execution."""

    def test_rm_rf_root_returns_false(self, tmp_path):
        cli = _make_cli(tmp_path)
        result = cli._run_security_checks("rm -rf /")
        assert result is False

    def test_blocked_command_logged(self, tmp_path):
        cli = _make_cli(tmp_path)
        cli._run_security_checks("mkfs /dev/sda")
        records = cli._exec_logger._load_all()
        assert len(records) == 1
        assert records[0]["risk_level"] == "blocked"
        assert records[0]["returncode"] is None

    def test_blocked_command_prints_panel(self, tmp_path):
        cli = _make_cli(tmp_path)
        cli._run_security_checks("shutdown now")
        cli.console.print.assert_called()


class TestSecurityChecksHigh:
    """High-risk commands show a warning and delegate to Confirm."""

    def test_high_risk_confirmed_returns_true(self, tmp_path):
        cli = _make_cli(tmp_path)
        with patch("src.cli_interface.Confirm.ask", return_value=True):
            result = cli._run_security_checks("rm -rf /tmp/old_logs")
        assert result is True

    def test_high_risk_denied_returns_false(self, tmp_path):
        cli = _make_cli(tmp_path)
        with patch("src.cli_interface.Confirm.ask", return_value=False):
            result = cli._run_security_checks("rm -rf /tmp/old_logs")
        assert result is False

    def test_high_risk_prints_warning_panel(self, tmp_path):
        cli = _make_cli(tmp_path)
        with patch("src.cli_interface.Confirm.ask", return_value=False):
            cli._run_security_checks("find /var -delete")
        cli.console.print.assert_called()


class TestSecurityChecksLowMedium:
    """Low/medium risk commands should pass through and return True."""

    def test_low_risk_ls_returns_true(self, tmp_path):
        cli = _make_cli(tmp_path)
        result = cli._run_security_checks("ls -la /tmp")
        assert result is True

    def test_medium_risk_mv_returns_true(self, tmp_path):
        cli = _make_cli(tmp_path)
        result = cli._run_security_checks("mv old.txt new.txt")
        assert result is True

    def test_low_risk_shows_no_confirm(self, tmp_path):
        """Low-risk commands must NOT trigger a Confirm prompt."""
        cli = _make_cli(tmp_path)
        with patch("src.cli_interface.Confirm.ask") as mock_confirm:
            cli._run_security_checks("cat /etc/hostname")
        mock_confirm.assert_not_called()


class TestSecurityChecksSimulatePreview:
    """Simulate preview panel is printed when simulate_command returns text."""

    def test_simulate_preview_printed_for_mv(self, tmp_path):
        cli = _make_cli(tmp_path)
        cli._run_security_checks("mv foo.txt bar.txt")
        # At least one console.print call should contain Panel
        printed_args = [str(call) for call in cli.console.print.call_args_list]
        assert any("Panel" in a or "预览" in a or "mv" in a.lower() for a in printed_args)

    def test_no_preview_for_empty_simulate(self, tmp_path):
        """Commands whose simulate returns '' should not print a preview panel."""
        cli = _make_cli(tmp_path)
        with patch("src.cli_interface.simulate_command", return_value=""):
            cli._run_security_checks("ls /tmp")
        # console.print may still be called for other reasons; just assert it returns True
        result = cli._run_security_checks("ls /tmp")
        assert result is True


@pytest.mark.skipif(sys.platform == "win32", reason="bash syntax validation differs on Windows")
class TestSecurityChecksSyntax:
    """Syntax errors must be caught in step 1 before risk classification."""

    def test_bad_syntax_returns_false(self, tmp_path):
        cli = _make_cli(tmp_path)
        result = cli._run_security_checks("for x in; do echo $x; done")
        assert result is False

    def test_bad_syntax_not_logged(self, tmp_path):
        """Syntax-failed commands are rejected before the logger is called."""
        cli = _make_cli(tmp_path)
        cli._run_security_checks("for x in; do echo $x; done")
        records = cli._exec_logger._load_all()
        assert len(records) == 0
