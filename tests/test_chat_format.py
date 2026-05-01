from pathlib import Path

from langchain_core.prompts import PromptTemplate

from memory.sqlite_memory import HierarchicalMemory
from src.shell_agent_client import SQLiteMemoryWrapper


def test_chat_prompt_contains_memory_sections(temp_db_path):
    mem = HierarchicalMemory(db_path=temp_db_path, session_id="chatfmt")
    wrapper = SQLiteMemoryWrapper(mem)

    wrapper.save_context({"input": "How do I list files?"}, {"output": "Use ls"})
    wrapper.save_context({"input": "Show hidden files too"}, {"output": "Use ls -a"})

    history = wrapper.load_memory_variables({"input": "sort by size"})

    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "shell_assistant.prompt"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    prompt = PromptTemplate(
        input_variables=["summary", "recent_history", "relevant_memory", "input", "target_shell"],
        template=prompt_text,
    )

    full_prompt = prompt.format(
        summary=history["summary"],
        recent_history=history["recent_history"],
        relevant_memory=history["relevant_memory"],
        input="sort by size",
        target_shell="bash",
    )

    assert "Recent conversation:" in full_prompt
    assert "Relevant context:" in full_prompt
    assert "How do I list files?" in full_prompt
    assert "Show hidden files too" in full_prompt
    assert "sort by size" in full_prompt
