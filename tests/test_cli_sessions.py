from src.cli_interface import ShellAgentCLI
from pathlib import Path


def _make_cli_for_sessions():
    cli = ShellAgentCLI.__new__(ShellAgentCLI)
    cli._custom_session_consumed = False
    cli._chat_store_path = Path(".") / "_unused_cli_test_store.json"
    cli._save_chat_state = lambda: None
    cli.chats = []
    cli._chat_counter = 0
    cli.active_chat_index = 0
    cli._create_chat(title="对话 1", switch_to=True)
    return cli


def test_create_chat_switches_to_new_session():
    cli = _make_cli_for_sessions()

    first_id = cli.session_id
    chat = cli._create_chat(title="项目A", switch_to=True)

    assert len(cli.chats) == 2
    assert cli.active_chat_index == 1
    assert cli.session_id == chat["session_id"]
    assert cli.session_id != first_id


def test_switch_chat_by_index_and_title():
    cli = _make_cli_for_sessions()
    cli._create_chat(title="项目A", switch_to=True)
    cli._create_chat(title="项目B", switch_to=True)

    assert cli._switch_chat("1") is True
    assert cli.active_chat_index == 0

    assert cli._switch_chat("项目A") is True
    assert cli.chats[cli.active_chat_index]["title"] == "项目A"

    assert cli._switch_chat("不存在") is False


def test_load_chat_state_restores_previous_sessions(tmp_path):
        store = tmp_path / "cli_chats.json"
        store.write_text(
                """
{
    "active_chat_index": 1,
    "chat_counter": 5,
    "chats": [
        {"title": "对话 1", "session_id": "s1"},
        {"title": "项目A", "session_id": "s2"}
    ]
}
""".strip(),
                encoding="utf-8",
        )

        cli = ShellAgentCLI.__new__(ShellAgentCLI)
        cli._custom_session_consumed = False
        cli._chat_store_path = store
        cli.chats = []
        cli._chat_counter = 0
        cli.active_chat_index = 0

        cli._load_chat_state()

        assert len(cli.chats) == 2
        assert cli.active_chat_index == 1
        assert cli.session_id == "s2"
