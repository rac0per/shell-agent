from memory.sqlite_memory import HierarchicalMemory
from src.shell_agent_client import SQLiteMemoryWrapper


class MockLLM:
    def __call__(self, user_input: str) -> str:
        prompt = user_input.lower()
        if "hidden" in prompt:
            return "ls -a"
        if "disk" in prompt:
            return "df -h"
        return "ls"


def test_mock_client_conversation_flow(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="mockflow", recent_limit=3)
    wrapper = SQLiteMemoryWrapper(mem)
    llm = MockLLM()

    queries = [
        "How to list files?",
        "How to show hidden files?",
        "How to check disk usage?",
    ]

    for q in queries:
        answer = llm(q)
        wrapper.save_context({"input": q}, {"output": answer})

    history = mem.get_recent_history(limit=10)

    assert len(history) == 6
    assert history[0]["role"] == "user"
    assert history[-1] == {"role": "assistant", "content": "df -h"}


def test_mock_client_relevant_memory_is_populated(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="mockrelevant", recent_limit=3)
    wrapper = SQLiteMemoryWrapper(mem)

    wrapper.save_context({"input": "show hidden files"}, {"output": "ls -a"})
    wrapper.save_context({"input": "check disk usage"}, {"output": "df -h"})

    context = wrapper.load_memory_variables({"input": "hidden"})

    assert "hidden" in context["relevant_memory"].lower() or "ls -a" in context["relevant_memory"].lower()
