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


def test_wrapper_merges_rag_retrieval(temp_db_path):
    class _DummyRetriever:
        def retrieve(self, query, top_k=4, category_filter=None):
            assert query == "how to list hidden files"
            assert top_k == 2
            return ["Use ls -a to include hidden files.", "Use ls -la for detailed output."]

    mem = HierarchicalMemory(db_path=temp_db_path, session_id="wrapper4")
    wrapper = SQLiteMemoryWrapper(mem, retriever=_DummyRetriever(), rag_top_k=2)

    loaded = wrapper.load_memory_variables({"input": "how to list hidden files"})

    assert "<doc>" in loaded["relevant_memory"]
    assert "Use ls -a to include hidden files." in loaded["relevant_memory"]


def test_wrapper_merges_rag_dict_docs(temp_db_path):
    """Retriever returning dict-format docs (content/source/score/category) are formatted correctly."""
    class _DictRetriever:
        def retrieve(self, query, top_k=4, category_filter=None):
            return [
                {"content": "Use grep -r for recursive search.", "source": "docs/commands/grep.md",
                 "category": "commands", "score": 0.92, "distance": 0.08},
            ]

    mem = HierarchicalMemory(db_path=temp_db_path, session_id="wrapper5")
    wrapper = SQLiteMemoryWrapper(mem, retriever=_DictRetriever())

    loaded = wrapper.load_memory_variables({"input": "recursive file search"})

    assert "Use grep -r" in loaded["relevant_memory"]
    assert "source=" in loaded["relevant_memory"]
