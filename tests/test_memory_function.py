from memory.sqlite_memory import HierarchicalMemory


def test_add_and_get_recent_history(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s1", recent_limit=5)

    mem.add_message("user", "hello")
    mem.add_message("assistant", "hi")

    history = mem.get_recent_history()

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "hi"}


def test_recent_history_respects_limit(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s2", recent_limit=1)

    mem.add_message("user", "q1")
    mem.add_message("assistant", "a1")
    mem.add_message("user", "q2")
    mem.add_message("assistant", "a2")

    history = mem.get_recent_history()

    # recent_limit is in turns, implementation fetches limit*2 messages.
    assert len(history) == 2
    assert history[0]["content"] == "q2"
    assert history[1]["content"] == "a2"


def test_relevant_history_by_keywords(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s3")

    mem.add_message("user", "How do I list hidden files?")
    mem.add_message("assistant", "Use ls -a")
    mem.add_message("user", "How to check disk usage?")
    mem.add_message("assistant", "Use df -h")

    relevant = mem.get_relevant_history("show hidden files")

    assert relevant
    assert any("hidden" in msg["content"].lower() for msg in relevant)


def test_get_memory_context_shapes_output(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s4")
    mem.update_summary("User asks shell basics")
    mem.add_message("user", "find files")
    mem.add_message("assistant", "use find . -name '*.txt'")

    context = mem.get_memory_context("find file name")

    assert context["summary"] == "User asks shell basics"
    assert "<user>" in context["recent_history"]
    assert "</assistant>" in context["recent_history"]
    assert isinstance(context["relevant_memory"], str)


def test_clear_history_resets_state(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s5")

    mem.add_message("user", "ls")
    mem.update_summary("summary")
    mem.clear_history()

    assert mem.get_recent_history() == []
    assert mem.get_relevant_history("ls") == []
    assert mem.summary == ""


def test_auto_summary_generated_when_not_manually_set(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="s6")

    mem.add_message("user", "列举目录下的所有文件")
    mem.add_message("assistant", '{"command":"ls -a"}')

    context = mem.get_memory_context("")
    assert context["summary"].startswith("用户近期关注：")
    assert "列举目录下的所有文件" in context["summary"]
