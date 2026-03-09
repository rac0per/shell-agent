import sys
import os
# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from memory.sqlite_memory import HierarchicalMemory
from src.shell_agent_client import SQLiteMemoryWrapper

def test_hierarchical_memory():
    print("Testing Hierarchical Memory System")
    print("=" * 50)

    # 初始化分层记忆
    memory_system = HierarchicalMemory(db_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/test_hierarchical.db")), recent_limit=3)
    memory = SQLiteMemoryWrapper(memory_system)

    # 添加一些对话历史
    conversations = [
        ("user", "How do I list files in current directory?"),
        ("assistant", "Use 'ls' command"),
        ("user", "Show me hidden files too"),
        ("assistant", "Use 'ls -a' to show all files including hidden ones"),
        ("user", "How to check disk usage?"),
        ("assistant", "Use 'df -h' command"),
        ("user", "What about file sizes?"),
        ("assistant", "Use 'du -sh *' to check sizes"),
        ("user", "How to find large files?"),
        ("assistant", "Use 'find . -size +100M' to find files larger than 100MB"),
    ]

    print("Adding conversation history...")
    for role, content in conversations:
        if role == "user":
            memory.save_context({"input": content}, {})
        else:
            memory.save_context({}, {"output": content})

    # 测试短期记忆（最近3轮）
    print("\n1. Recent History (last 3 turns):")
    context = memory.load_memory_variables({"input": ""})
    print(context["recent_history"])

    # 测试相关记忆检索
    print("\n2. Relevant Memory for 'file size':")
    context = memory.load_memory_variables({"input": "How to check file sizes?"})
    print(context["relevant_memory"])

    # 测试完整上下文
    print("\n3. Full Context Structure:")
    context = memory.load_memory_variables({"input": "Show me commands for file operations"})
    for key, value in context.items():
        print(f"{key}:")
        print(f"  {value[:100]}{'...' if len(value) > 100 else ''}")
        print()

    # 测试总结功能
    print("4. Testing Summary Feature:")
    memory_system.update_summary("User is learning basic shell commands for file operations.")
    context = memory.load_memory_variables({"input": ""})
    print(f"Summary: {context['summary']}")

if __name__ == "__main__":
    test_hierarchical_memory()