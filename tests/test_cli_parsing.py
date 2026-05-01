from src.cli_interface import ShellAgentCLI


def _make_cli_without_init():
    # parse_response and check_command_safety do not depend on __init__ state.
    return ShellAgentCLI.__new__(ShellAgentCLI)


def test_parse_response_plain_json():
    cli = _make_cli_without_init()

    result = cli.parse_response(
        '{"command": "ls -la", "explanation": "list files", "warning": ""}'
    )

    assert result["command"] == "ls -la"
    assert result["explanation"] == "list files"
    assert result["warning"] == ""


def test_parse_response_markdown_json_block():
    cli = _make_cli_without_init()

    payload = '{"command": "find . -name \\\"*.txt\\\"", "explanation": "find txt", "warning": "slow"}'
    result = cli.parse_response(
        f"""```json
        {payload}
        ```"""
    )

    assert result == {
        "command": 'find . -name "*.txt"',
        "explanation": "find txt",
        "warning": "slow",
    }


def test_parse_response_invalid_json_returns_warning():
    cli = _make_cli_without_init()

    result = cli.parse_response("not a json payload")

    assert result["command"] == ""
    assert result["warning"] == "模型回复格式非法，未能识别 JSON"
    assert result["explanation"] == "not a json payload"


def test_parse_response_recovers_from_invalid_escape_sequence():
    cli = _make_cli_without_init()

    payload = '{"command":"rm -rf /\\*","explanation":"danger","warning":"do not run"}'
    result = cli.parse_response(payload)

    assert result["command"] == "rm -rf /*"
    assert result["explanation"] == "danger"
    assert result["warning"] == "do not run"


def test_parse_response_field_level_fallback_for_broken_json():
    cli = _make_cli_without_init()

    # Missing comma between explanation and warning keeps JSON invalid.
    payload = '{"command":"ls","explanation":"list files" "warning":""}'
    result = cli.parse_response(payload)

    assert result["command"] == "ls"
    assert result["explanation"] == "list files"
    assert result["warning"] in ("", "模型回复格式部分异常，已尝试容错解析")


def test_parse_response_labeled_text_format_chinese():
    cli = _make_cli_without_init()

    payload = (
        "命令: wget https://dl.google.com/chrome/install/linux.GoogleChrome.stable.x86_64.rpm\n"
        "说明: 使用wget下载Chrome安装包\n"
        "警告: 链接可能过期"
    )
    result = cli.parse_response(payload)

    assert result["command"].startswith("wget https://dl.google.com/chrome")
    assert result["explanation"] == "使用wget下载Chrome安装包"
    assert result["warning"] == "链接可能过期"


def test_parse_response_labeled_text_without_warning_adds_default_warning():
    cli = _make_cli_without_init()

    payload = "command: ls -la\nexplanation: list all files"
    result = cli.parse_response(payload)

    assert result["command"] == "ls -la"
    assert result["explanation"] == "list all files"
    assert result["warning"] == "模型回复非JSON，已按标签容错解析"


def test_parse_response_greeting_explanation_only_has_no_fake_command_and_no_warning():
    cli = _make_cli_without_init()

    payload = "说明: 回应用户问候"
    result = cli.parse_response(payload)

    assert result["command"] == ""
    assert result["explanation"] == "回应用户问候"
    assert result["warning"] == ""


def test_parse_response_non_command_in_command_field_is_downgraded_to_explanation():
    cli = _make_cli_without_init()

    payload = '{"command":"回应用户问候","explanation":"","warning":""}'
    result = cli.parse_response(payload)

    assert result["command"] == ""
    assert result["explanation"] == "回应用户问候"
    assert result["warning"] == ""


def test_parse_response_uses_first_json_object_when_wrapped_text():
    cli = _make_cli_without_init()

    payload = 'prefix {"command":"pwd","explanation":"show dir","warning":""} suffix'
    result = cli.parse_response(payload)

    assert result["command"] == "pwd"
    assert result["explanation"] == "show dir"


def test_parse_response_empty_json_object_has_visible_fallback_message():
    cli = _make_cli_without_init()

    result = cli.parse_response("{}")

    assert result["command"] == ""
    assert result["explanation"] == "请重试一次；如果问题持续，请检查模型服务状态。"
    assert result["warning"] == "模型回复为空，未返回可执行命令或说明"


def test_parse_response_blank_text_has_visible_fallback_message():
    cli = _make_cli_without_init()

    result = cli.parse_response("   ")

    assert result["command"] == ""
    assert result["explanation"] == "请重试一次；如果问题持续，请检查模型服务状态。"
    assert result["warning"] == "模型回复为空，未返回可执行命令或说明"


def test_check_command_safety_blocks_dangerous_patterns():
    cli = _make_cli_without_init()

    assert cli.check_command_safety("rm -rf /") is False
    assert cli.check_command_safety("echo ok && reboot") is False


def test_check_command_safety_allows_normal_commands():
    cli = _make_cli_without_init()

    assert cli.check_command_safety("ls -la") is True
    assert cli.check_command_safety("find . -type f") is True
