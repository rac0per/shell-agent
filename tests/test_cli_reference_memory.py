from src.cli_interface import ShellAgentCLI


class _FakeLLM:
    def __init__(self):
        self.last_input = ""

    def generate_command(self, user_input: str, session_id: str, target_shell: str):
        self.last_input = user_input
        return '{"command":"mv ./a.log ./b.tar /data/backup/","explanation":"move files","warning":""}'


def _make_cli_for_reference_tests():
    cli = ShellAgentCLI.__new__(ShellAgentCLI)
    cli.target_shell = "bash"
    cli.session_id = "s_ref"
    cli.llm = _FakeLLM()
    cli._working_memory = cli._init_working_memory()
    return cli


def test_reference_query_uses_previous_items_to_generate_mv():
    cli = _make_cli_for_reference_tests()

    cli._update_working_memory(
        "find . -type f -size +100M",
        "./a.log\n./b.tar\n",
    )

    parsed = cli._generate_from_user_input("将这些文件移动到 /data/backup 目录")

    assert parsed["command"].startswith("mv ")
    assert "./a.log" in parsed["command"]
    assert "./b.tar" in parsed["command"]
    assert "/data/backup/" in parsed["command"]
    assert "WORKING_MEMORY" in cli.llm.last_input
    assert "./a.log" in cli.llm.last_input


def test_reference_query_without_entities_returns_clear_message():
    cli = _make_cli_for_reference_tests()

    parsed = cli._generate_from_user_input("把这些文件移动到 /data/backup")

    assert parsed["command"] == ""
    assert "缺少可引用的上一步结果" in parsed["explanation"]
    assert "指代消解" in parsed["warning"]
