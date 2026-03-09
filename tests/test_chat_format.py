import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory.sqlite_memory import SQLiteMemory
from shell_agent_client import SQLiteMemoryWrapper
from langchain_core.prompts import PromptTemplate
from pathlib import Path

def test_chat_format():
    print("Testing Chat Format Memory System")
    print("=" * 50)

    # 初始化记忆系统
    sqlite_mem = SQLiteMemory(db_path="../data/test_chat_format.db")
    memory = SQLiteMemoryWrapper(sqlite_mem)

    # 模拟对话历史
    memory.save_context({"input": "How do I list files?"}, {"output": "Use the 'ls' command"})
    memory.save_context({"input": "Show hidden files too"}, {"output": "Use 'ls -a' for all files including hidden ones"})

    # 加载记忆变量
    history = memory.load_memory_variables({})
    print("Current conversation history:")
    print(history["history"])
    print()

    # 模拟构建prompt
    prompt_text = Path("../prompts/shell_assistant.prompt").read_text(encoding="utf-8")
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=prompt_text,
    )

    # 测试新输入的完整prompt
    test_input = "What about sorting by size?"
    full_prompt = prompt.format(history=history["history"], input=test_input)

    print("Full prompt that would be sent to LLM:")
    print("-" * 50)
    print(full_prompt)
    print("-" * 50)

if __name__ == "__main__":
    test_chat_format()