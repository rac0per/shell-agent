from memory.sqlite_memory import HierarchicalMemory
from src.shell_agent_client import SQLiteMemoryWrapper


def test_hierarchical_memory_context_sections(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="hier1", recent_limit=3)
    wrapper = SQLiteMemoryWrapper(mem)

    conversations = [
        ("How do I list files in current directory?", "Use ls"),
        ("Show me hidden files too", "Use ls -a"),
        ("How to check disk usage?", "Use df -h"),
    ]

    for user_msg, assistant_msg in conversations:
        wrapper.save_context({"input": user_msg}, {"output": assistant_msg})

    context = wrapper.load_memory_variables({"input": "hidden files"})

    assert "<user>" in context["recent_history"]
    assert "<assistant>" in context["recent_history"]
    assert "Show me hidden files too" in context["recent_history"]
    assert isinstance(context["relevant_memory"], str)


def test_hierarchical_memory_summary_update(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="hier2")
    wrapper = SQLiteMemoryWrapper(mem)

    mem.update_summary("User is learning shell command basics")
    context = wrapper.load_memory_variables({"input": ""})

    assert context["summary"] == "User is learning shell command basics"
