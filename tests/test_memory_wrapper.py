from memory.sqlite_memory import HierarchicalMemory
from src.shell_agent_client import SQLiteMemoryWrapper


def test_wrapper_save_context_adds_user_and_assistant(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="wrapper1")
    wrapper = SQLiteMemoryWrapper(mem)

    wrapper.save_context({"input": "hello"}, {"output": "hi"})

    history = mem.get_recent_history()
    assert history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_wrapper_load_memory_variables_contains_compat_history(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="wrapper2")
    wrapper = SQLiteMemoryWrapper(mem)

    wrapper.save_context({"input": "show hidden files"}, {"output": "ls -a"})
    loaded = wrapper.load_memory_variables({"input": "hidden"})

    assert set(["summary", "recent_history", "relevant_memory", "history"]).issubset(loaded.keys())
    assert loaded["history"] == loaded["recent_history"]
    assert isinstance(loaded["relevant_memory"], str)


def test_wrapper_clear_deletes_history(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="wrapper3")
    wrapper = SQLiteMemoryWrapper(mem)

    wrapper.save_context({"input": "q"}, {"output": "a"})
    wrapper.clear()

    loaded = wrapper.load_memory_variables({"input": "q"})
    assert loaded["recent_history"] == ""
    assert loaded["summary"] == ""
