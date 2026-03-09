import sys
import os
# Add both src and memory directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory.sqlite_memory import SQLiteMemory
from shell_agent_client import SQLiteMemoryWrapper

# 测试 SQLiteMemoryWrapper
def test_memory_wrapper():
    # 初始化
    sqlite_mem = SQLiteMemory(db_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/test_memory_wrapper.db")))
    memory = SQLiteMemoryWrapper(sqlite_mem)

    # 添加上下文
    memory.save_context({"input": "Hello"}, {"output": "Hi there!"})
    memory.save_context({"input": "How are you?"}, {"output": "I'm doing well, thank you!"})

    # 加载记忆变量
    vars = memory.load_memory_variables({})
    print("Memory variables:")
    print(vars)

    # 再次添加
    memory.save_context({"input": "What's the weather like?"}, {"output": "I don't have access to weather data."})

    vars = memory.load_memory_variables({})
    print("\nUpdated memory variables:")
    print(vars)

    # 清除
    memory.clear()
    vars = memory.load_memory_variables({})
    print(f"\nAfter clear: {vars}")

if __name__ == "__main__":
    test_memory_wrapper()