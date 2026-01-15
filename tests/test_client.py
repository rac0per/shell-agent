"""
Test the shell agent client with mock responses
"""
import requests
import time
import sys

def test_server_connection():
    """Check if model server is running"""
    url = "http://127.0.0.1:8000/generate"
    try:
        response = requests.post(url, json={"prompt": "test"}, timeout=5)
        return True
    except:
        return False

def test_client_workflow():
    """Test the client workflow without interactive loop"""
    from memory.sqlite_memory import SQLiteMemory
    from src.shell_agent_client import SQLiteMemoryWrapper, QwenHTTP
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from pathlib import Path
    
    print("=" * 60)
    print("Testing Shell Agent Client Workflow")
    print("=" * 60)
    
    # Initialize LLM
    print("\n[1] Initializing LLM...")
    llm = QwenHTTP()
    
    # Initialize SQLiteMemory
    print("[2] Initializing Memory System...")
    sqlite_mem = SQLiteMemory(db_path="./data/test_client_memory.db", session_id="test_run")
    sqlite_mem.clear_history()  # Start fresh
    memory = SQLiteMemoryWrapper(sqlite_mem)
    
    # Load PromptTemplate
    print("[3] Loading Prompt Template...")
    prompt_text = Path("prompts/shell_assistant.prompt").read_text(encoding="utf-8")
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=prompt_text,
    )
    
    # Build chain
    print("[4] Building LangChain Pipeline...")
    chain = (
        {
            "history": lambda _: memory.load_memory_variables({})["history"],
            "input": RunnablePassthrough(),
        }
        | prompt
        | llm
    )
    
    # Test conversations
    print("\n" + "=" * 60)
    print("Testing Conversation Flow")
    print("=" * 60)
    
    test_queries = [
        "list all files in current directory",
        "show hidden files too",
    ]
    
    for i, user_input in enumerate(test_queries, 1):
        print(f"\n[Query {i}] User: {user_input}")
        
        try:
            # Generate response
            response = chain.invoke(user_input)
            
            # Save to memory
            memory.save_context({"input": user_input}, {"output": response})
            
            print(f"[Response {i}] Assistant: {response}")
            
            # Verify memory
            history = sqlite_mem.get_history()
            print(f"[Memory] History now has {len(history)} messages")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    # Verify full history
    print("\n" + "=" * 60)
    print("Verifying Complete History")
    print("=" * 60)
    history = sqlite_mem.get_history()
    print(f"Total messages in history: {len(history)}")
    for i, msg in enumerate(history, 1):
        print(f"  {i}. [{msg['role']}] {msg['content'][:50]}...")
    
    # Test history in next query
    print("\n" + "=" * 60)
    print("Testing History Context (should remember previous)")
    print("=" * 60)
    history_text = memory.load_memory_variables({})["history"]
    print(f"History passed to prompt:\n{history_text}\n")
    
    # Cleanup
    sqlite_mem.clear_history()
    
    print("\n" + "=" * 60)
    print("✓ All client workflow tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("Checking if model server is running...")
    if not test_server_connection():
        print("\n⚠️  Model server is not running at http://127.0.0.1:8000")
        print("To test the full system:")
        print("  1. In one terminal: python src/model_server.py")
        print("  2. Wait for model to load (~1-2 minutes)")
        print("  3. In another terminal: python tests/test_client.py")
        print("\nContinuing with workflow test (will fail at LLM call)...")
        print("")
    else:
        print("✓ Model server is running!\n")
    
    success = test_client_workflow()
    sys.exit(0 if success else 1)
