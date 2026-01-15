import requests
from memory.sqlite_memory import SQLiteMemory
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain import BaseMemory
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path
from typing import Dict, Any, List

# ==========================
# 自定义 LangChain Memory
# ==========================
class SQLiteMemoryWrapper(BaseMemory):
    """
    继承 BaseMemory，使 SQLiteMemory 可作为 LangChain Memory 使用
    """
    def __init__(self, sqlite_memory: SQLiteMemory):
        self.sqlite_memory = sqlite_memory
        self.memory_key = "history"

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        history = self.sqlite_memory.get_history()
        history_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history])
        return {self.memory_key: history_text}

    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]) -> None:
        if "input" in inputs:
            self.sqlite_memory.add_message("user", inputs["input"])
        if "output" in outputs:
            self.sqlite_memory.add_message("assistant", outputs["output"])

    def clear(self) -> None:
        self.sqlite_memory.clear_history()

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
    sqlite_mem = SQLiteMemory(db_path="./data/memory.db")
    memory = SQLiteMemoryWrapper(sqlite_mem)

    # 加载 PromptTemplate
    prompt_text = load_prompt("prompts/shell_assistant.prompt")
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=prompt_text,
    )

    # 构建 LangChain 流水线
    chain = (
        {
            "history": lambda _: memory.load_memory_variables({})["history"],
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
