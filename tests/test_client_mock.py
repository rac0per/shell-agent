import sys
import os
# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory.sqlite_memory import HierarchicalMemory
from shell_agent_client import SQLiteMemoryWrapper
from langchain_core.prompts import PromptTemplate
from pathlib import Path

# Mock LLM for testing
class MockLLM:
    def __call__(self, prompt: str) -> str:
        # Simple mock response based on prompt content
        prompt_lower = prompt.lower()
        if "list files" in prompt_lower and "hidden" not in prompt_lower:
            return "ls"
        elif "hidden files" in prompt_lower:
            return "ls -a"
        elif "file size" in prompt_lower:
            return "du -sh *"
        elif "disk usage" in prompt_lower:
            return "df -h"
        else:
            return "echo 'Command not recognized'"

def test_shell_agent_client():
    print("Testing Shell Agent Client with Mock LLM")
    print("=" * 50)

    # Initialize memory system
    memory_system = HierarchicalMemory(db_path="../data/test_client.db", recent_limit=3)
    memory = SQLiteMemoryWrapper(memory_system)

    # Set initial summary
    memory_system.update_summary("User is learning shell commands for file operations.")

    # Load prompt template
    prompt_text = Path("../prompts/shell_assistant.prompt").read_text(encoding="utf-8")
    prompt = PromptTemplate(
        input_variables=["summary", "recent_history", "relevant_memory", "input"],
        template=prompt_text,
    )

    # Initialize mock LLM
    llm = MockLLM()

    # Test conversation flow
    test_queries = [
        "How do I list files in current directory?",
        "Show me hidden files too",
        "What about checking file sizes?",
        "How to check disk usage?"
    ]

    expected_responses = [
        "ls",
        "ls -a",
        "du -sh *",
        "df -h"
    ]

    print(" Starting conversation...")
    print()

    for i, (user_input, expected) in enumerate(zip(test_queries, expected_responses), 1):
        print(f"[{i}] User: {user_input}")

        # Get memory context
        context = memory.load_memory_variables({"input": user_input})

        # Format prompt
        full_prompt = prompt.format(
            summary=context["summary"],
            recent_history=context["recent_history"],
            relevant_memory=context["relevant_memory"],
            input=user_input
        )

        # Get LLM response (mock based on user input only)
        response = llm(user_input)  # 只检查用户输入
        print(f"[{i}] Assistant: {response} (expected: {expected})")

        # Save to memory
        memory.save_context({"input": user_input}, {"output": response})
        print()

    print("Test completed successfully!")
    print("\n Memory Statistics:")
    context = memory.load_memory_variables({"input": ""})
    print(f"Summary: {context['summary']}")
    print(f"Recent history length: {len(context['recent_history'])} chars")
    print(f"Relevant memory length: {len(context['relevant_memory'])} chars")

if __name__ == "__main__":
    test_shell_agent_client()