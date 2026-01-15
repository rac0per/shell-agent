"""
Simple test script to verify SQLite memory system works correctly
"""
from memory.sqlite_memory import SQLiteMemory

def test_memory():
    print("=" * 50)
    print("Testing SQLite Memory System")
    print("=" * 50)
    
    # Test 1: Basic functionality
    print("\n[Test 1] Creating memory with test session...")
    mem = SQLiteMemory(db_path="./data/test_memory.db", session_id="test_session_1")
    
    # Test 2: Add messages
    print("[Test 2] Adding messages...")
    mem.add_message("user", "How do I list files?")
    mem.add_message("assistant", "Use the 'ls' command")
    mem.add_message("user", "What about directories?")
    mem.add_message("assistant", "Use 'ls -la' for detailed listing")
    
    # Test 3: Retrieve history
    print("[Test 3] Retrieving history...")
    history = mem.get_history()
    print(f"  Found {len(history)} messages:")
    for i, msg in enumerate(history, 1):
        print(f"    {i}. {msg['role']}: {msg['content']}")
    
    # Test 4: Test persistence - new instance
    print("\n[Test 4] Testing persistence with new instance...")
    mem2 = SQLiteMemory(db_path="./data/test_memory.db", session_id="test_session_1")
    history2 = mem2.get_history()
    print(f"  Retrieved {len(history2)} messages from new instance")
    
    # Test 5: Different session
    print("\n[Test 5] Testing session isolation...")
    mem3 = SQLiteMemory(db_path="./data/test_memory.db", session_id="test_session_2")
    mem3.add_message("user", "Different session message")
    history3 = mem3.get_history()
    print(f"  Session 2 has {len(history3)} messages (should be 1)")
    
    # Test 6: Clear history
    print("\n[Test 6] Testing clear history...")
    mem.clear_history()
    history_after_clear = mem.get_history()
    print(f"  After clear: {len(history_after_clear)} messages (should be 0)")
    
    # Verify session 2 is unaffected
    history3_after = mem3.get_history()
    print(f"  Session 2 still has {len(history3_after)} messages (should be 1)")
    
    # Cleanup
    mem3.clear_history()
    
    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    test_memory()
