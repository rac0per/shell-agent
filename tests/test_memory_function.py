import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory.sqlite_memory import SQLiteMemory

# 测试 SQLiteMemory
def test_memory():
    # 初始化
    mem = SQLiteMemory(db_path="../data/test_memory.db")

    # 添加消息
    mem.add_message("user", "Hello")
    mem.add_message("assistant", "Hi there!")

    # 获取历史
    history = mem.get_history()
    print("History after adding messages:")
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")

    # 再次添加
    mem.add_message("user", "How are you?")
    mem.add_message("assistant", "I'm doing well, thank you!")

    # 获取历史
    history = mem.get_history()
    print("\nHistory after more messages:")
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")

    # 测试清除
    mem.clear_history()
    history = mem.get_history()
    print(f"\nHistory after clear: {len(history)} messages")

if __name__ == "__main__":
    test_memory()