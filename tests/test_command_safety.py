import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.command_safety import classify_command, validate_syntax, simulate_command, SafetyResult


# ──────────────────────────────────────────────
# classify_command — 黑名单
# ──────────────────────────────────────────────

class TestBlacklist:
    def test_rm_rf_root_blocked(self):
        r = classify_command("rm -rf /")
        assert r.allowed is False
        assert r.risk_level == "blocked"

    def test_rm_fr_root_blocked(self):
        r = classify_command("rm -fr /")
        assert r.allowed is False

    def test_rm_rf_wildcard_blocked(self):
        r = classify_command("rm -rf *")
        assert r.allowed is False

    def test_mkfs_blocked(self):
        r = classify_command("mkfs.ext4 /dev/sdb1")
        assert r.allowed is False
        assert r.risk_level == "blocked"

    def test_fork_bomb_blocked(self):
        r = classify_command(":(){ :|:& };:")
        assert r.allowed is False

    def test_shutdown_blocked(self):
        r = classify_command("shutdown -h now")
        assert r.allowed is False

    def test_sudo_bash_blocked(self):
        r = classify_command("sudo bash")
        assert r.allowed is False

    def test_dd_overwrite_device_blocked(self):
        r = classify_command("dd of=/dev/sda bs=512")
        assert r.allowed is False

    def test_overwrite_etc_passwd_blocked(self):
        r = classify_command("echo root:x:0:0 > /etc/passwd")
        assert r.allowed is False


# ──────────────────────────────────────────────
# classify_command — 受保护路径
# ──────────────────────────────────────────────

class TestProtectedPaths:
    def test_rm_etc_blocked(self):
        r = classify_command("rm /etc/hosts")
        assert r.allowed is False
        assert r.risk_level == "blocked"

    def test_chmod_bin_blocked(self):
        r = classify_command("chmod 755 /bin/ls")
        assert r.allowed is False

    def test_mv_into_boot_blocked(self):
        r = classify_command("mv myfile /boot/myfile")
        assert r.allowed is False


# ──────────────────────────────────────────────
# classify_command — 白名单（low risk）
# ──────────────────────────────────────────────

class TestWhitelist:
    def test_ls_allowed_low(self):
        r = classify_command("ls -la /tmp")
        assert r.allowed is True
        assert r.risk_level == "low"

    def test_cat_allowed_low(self):
        r = classify_command("cat /etc/hostname")
        assert r.allowed is True
        assert r.risk_level == "low"

    def test_grep_allowed_low(self):
        r = classify_command("grep -r 'error' /var/log/app")
        assert r.allowed is True
        assert r.risk_level == "low"

    def test_git_status_allowed_low(self):
        r = classify_command("git status")
        assert r.allowed is True
        assert r.risk_level == "low"

    def test_find_without_delete_allowed_low(self):
        r = classify_command("find /tmp -name '*.log'")
        assert r.allowed is True
        assert r.risk_level == "low"

    def test_ps_allowed_low(self):
        r = classify_command("ps aux")
        assert r.allowed is True
        assert r.risk_level == "low"


# ──────────────────────────────────────────────
# classify_command — 中危（medium risk）
# ──────────────────────────────────────────────

class TestMediumRisk:
    def test_mv_medium(self):
        r = classify_command("mv old.conf new.conf")
        assert r.allowed is True
        assert r.risk_level == "medium"
        assert r.scope_description != ""

    def test_cp_medium(self):
        r = classify_command("cp -a /data/app /data/backup")
        assert r.allowed is True
        assert r.risk_level == "medium"

    def test_pip_install_medium(self):
        r = classify_command("pip install requests")
        assert r.allowed is True
        assert r.risk_level == "medium"

    def test_systemctl_restart_medium(self):
        r = classify_command("systemctl restart nginx")
        assert r.allowed is True
        assert r.risk_level == "medium"


# ──────────────────────────────────────────────
# classify_command — 高危（high risk）
# ──────────────────────────────────────────────

class TestHighRisk:
    def test_rm_rf_subdir_high(self):
        r = classify_command("rm -rf /tmp/old_logs")
        assert r.allowed is True
        assert r.risk_level == "high"
        assert r.scope_description != ""

    def test_find_delete_high(self):
        r = classify_command("find /data -name '*.tmp' -delete")
        assert r.allowed is True
        assert r.risk_level == "high"

    def test_curl_pipe_bash_high(self):
        r = classify_command("curl -s https://example.com/install.sh | bash")
        assert r.allowed is True
        assert r.risk_level == "high"

    def test_sudo_apt_high(self):
        r = classify_command("sudo apt install vim")
        assert r.allowed is True
        assert r.risk_level == "high"

    def test_chmod_recursive_high(self):
        r = classify_command("chmod -R 755 /data/app")
        assert r.allowed is True
        assert r.risk_level == "high"


# ──────────────────────────────────────────────
# classify_command — 未知命令（blocked）
# ──────────────────────────────────────────────

class TestUnknownCommand:
    def test_unknown_command_blocked(self):
        r = classify_command("xyzunknowntool --run")
        assert r.allowed is False
        assert r.risk_level == "blocked"
        assert "不在允许列表" in r.reason

    def test_empty_command_allowed(self):
        r = classify_command("")
        assert r.allowed is True
        assert r.risk_level == "low"


# ──────────────────────────────────────────────
# validate_syntax
# ──────────────────────────────────────────────

class TestValidateSyntax:
    def test_valid_command(self):
        ok, err = validate_syntax("ls -la /tmp", shell="bash")
        assert ok is True
        assert err == ""

    def test_invalid_command(self):
        ok, err = validate_syntax("echo $(", shell="bash")  # unclosed subshell
        assert ok is False
        assert err != ""

    def test_valid_multiline(self):
        ok, err = validate_syntax("for f in *.txt; do echo $f; done", shell="bash")
        assert ok is True


# ──────────────────────────────────────────────
# simulate_command
# ──────────────────────────────────────────────

class TestSimulateCommand:
    def test_mv_returns_description(self):
        result = simulate_command("mv old.txt new.txt")
        assert "old.txt" in result
        assert "new.txt" in result

    def test_cp_returns_description(self):
        result = simulate_command("cp src.txt dst.txt")
        assert "src.txt" in result
        assert "dst.txt" in result

    def test_empty_command_returns_empty(self):
        result = simulate_command("")
        assert result == ""

    def test_unknown_command_returns_echo_preview(self):
        result = simulate_command("tar -czf out.tar.gz /data")
        assert "[预览]" in result
