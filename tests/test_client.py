"""
Test the shell agent client with mock responses
"""
import requests
import time
import sys
import os

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
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
    sqlite_mem = SQLiteMemory(db_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/test_client_memory.db")), session_id="test_run")
    sqlite_mem.clear_history()  # Start fresh
    memory = SQLiteMemoryWrapper(sqlite_mem)
    
    # Load PromptTemplate
    print("[3] Loading Prompt Template...")
    prompt_text = Path(os.path.join(os.path.dirname(__file__), "../prompts/shell_assistant.prompt")).read_text(encoding="utf-8")
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=prompt_text,
    )
    
    # Build chain
    print("[4] Building LangChain Pipeline...")
    def get_memory_vars(input_text):
        return memory.load_memory_variables({"input": input_text})
    
    from langchain_core.runnables import RunnableLambda
    chain = (
        RunnableLambda(lambda x: {"input": x})
        | RunnablePassthrough.assign(
            summary=lambda x: get_memory_vars("")["summary"],
            recent_history=lambda x: get_memory_vars("")["recent_history"],
            relevant_memory=lambda x: get_memory_vars(x["input"])["relevant_memory"],
        )
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
            history = sqlite_mem.get_recent_history()
            print(f"[Memory] History now has {len(history)} messages")
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    # Verify full history
    print("\n" + "=" * 60)
    print("Verifying Complete History")
    print("=" * 60)
    history = sqlite_mem.get_recent_history()
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
    print("All client workflow tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("Checking if model server is running...")
    if not test_server_connection():
        print("\n  Model server is not running at http://127.0.0.1:8000")
        print("To test the full system:")
        print("  1. In one terminal: python src/model_server.py")
        print("  2. Wait for model to load (~1-2 minutes)")
        print("  3. In another terminal: python tests/test_client.py")
        print("\nContinuing with workflow test (will fail at LLM call)...")
        print("")
    else:
        print("Model server is running!\n")
    
    success = test_client_workflow()
    sys.exit(0 if success else 1)
