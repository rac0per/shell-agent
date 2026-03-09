import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from memory.sqlite_memory import SQLiteMemory
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path
from typing import Dict, Any, List

# ==========================
# 自定义 LangChain Memory
# ==========================
class SQLiteMemoryWrapper:
    """
    包装 HierarchicalMemory，使其可作为 LangChain Memory 使用
    支持分层记忆：summary + recent_history + relevant_memory
    """
    def __init__(self, hierarchical_memory):
        self.hierarchical_memory = hierarchical_memory
        self.memory_keys = ["summary", "recent_history", "relevant_memory"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        current_input = inputs.get("input", "") if inputs else ""
        memory_context = self.hierarchical_memory.get_memory_context(current_input)
        return memory_context

    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]) -> None:
        if "input" in inputs:
            self.hierarchical_memory.add_message("user", inputs["input"])
        if "output" in outputs:
            self.hierarchical_memory.add_message("assistant", outputs["output"])

    def clear(self) -> None:
        self.hierarchical_memory.clear_history()

# ==========================
# 自定义 LLM
# ==========================
url = "http://127.0.0.1:8000/generate"

class QwenHTTP(LLM):
    @property
    def _llm_type(self) -> str:
        return "qwen_http"

    def _call(self, prompt: str, stop=None) -> str:
        resp = requests.post(url, json={"prompt": prompt, "max_new_tokens": 256}, timeout=300)
        resp.raise_for_status()
        return resp.json()["response"]

# ==========================
# 辅助函数：加载 Prompt
# ==========================
def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

# ==========================
# 主程序
# ==========================
def main():
    # 初始化 LLM
    llm = QwenHTTP()

    # 初始化 SQLiteMemory
    sqlite_mem = SQLiteMemory(db_path="../data/memory.db")
    memory = SQLiteMemoryWrapper(sqlite_mem)

    # 加载 PromptTemplate
    prompt_text = load_prompt("../prompts/shell_assistant.prompt")
    prompt = PromptTemplate(
        input_variables=["summary", "recent_history", "relevant_memory", "input"],
        template=prompt_text,
    )

    # 构建 LangChain 流水线
    chain = (
        {
            "summary": lambda _: memory.load_memory_variables({"input": ""})["summary"],
            "recent_history": lambda _: memory.load_memory_variables({"input": ""})["recent_history"],
            "relevant_memory": lambda x: memory.load_memory_variables({"input": x})["relevant_memory"],
            "input": RunnablePassthrough(),
        }
        | prompt
        | llm
    )

    print("Shell assistant ready. Type 'exit' to quit.")
    while True:
        user_input = input("User: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break

        # 调用 chain 生成
        response = chain.invoke(user_input)

        # 保存到 SQLiteMemory
        memory.save_context({"input": user_input}, {"output": response})

        print(f"Assistant: {response}")
        print("--------------------------------")

if __name__ == "__main__":
    main()
