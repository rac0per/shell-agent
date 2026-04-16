import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from memory.sqlite_memory import SQLiteMemory
from src.rag_routing import detect_rag_category
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import PromptTemplate
from pathlib import Path
from typing import Dict, Any, List, Optional, Protocol
from pydantic import PrivateAttr

# ==========================
# 自定义 LangChain Memory
# ==========================
class RetrieverProtocol(Protocol):
    """Minimal retriever protocol for injecting RAG context."""

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        ...


class SQLiteMemoryWrapper:
    """
    包装 HierarchicalMemory，使其可作为 LangChain Memory 使用
    支持分层记忆：summary + recent_history + relevant_memory
    """
    def __init__(
        self,
        hierarchical_memory,
        retriever: Optional[RetrieverProtocol] = None,
        rag_top_k: int = 4,
    ):
        self.hierarchical_memory = hierarchical_memory
        self.memory_keys = ["summary", "recent_history", "relevant_memory"]
        self.retriever = retriever
        self.rag_top_k = rag_top_k

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        current_input = inputs.get("input", "") if inputs else ""
        memory_context = self.hierarchical_memory.get_memory_context(current_input)

        if self.retriever and current_input.strip():
            rag_docs = self.retriever.retrieve(current_input, top_k=self.rag_top_k)
            if rag_docs:
                rag_blocks: List[str] = []
                for doc in rag_docs:
                    if isinstance(doc, str):
                        rag_blocks.append(f"<doc>\n{doc}\n</doc>")
                        continue

                    content = str(doc.get("content", "")).strip()
                    if not content:
                        continue

                    source = str(doc.get("source", "")).strip()
                    score = doc.get("score")
                    score_text = f" score={float(score):.4f}" if isinstance(score, (int, float)) else ""
                    source_line = f"source={source}{score_text}" if source else f"source=unknown{score_text}"
                    rag_blocks.append(f"<doc {source_line}>\n{content}\n</doc>")

                rag_text = "\n".join(rag_blocks)
                existing = memory_context.get("relevant_memory", "")
                memory_context["relevant_memory"] = (
                    f"{existing}\n{rag_text}".strip() if existing else rag_text
                )

        # Add 'history' for backward compatibility
        memory_context["history"] = memory_context["recent_history"]
        return memory_context

    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]) -> None:
        if "input" in inputs:
            self.hierarchical_memory.add_message("user", inputs["input"])
        if "output" in outputs:
            self.hierarchical_memory.add_message("assistant", outputs["output"])

    def clear(self) -> None:
        self.hierarchical_memory.clear_history()


# ------------------------------------------------------------------
# Category routing helper (mirrors model_server._detect_rag_category)
# ------------------------------------------------------------------

def _detect_rag_category(user_input: str) -> Optional[str]:
    return detect_rag_category(user_input)

# ==========================
# 自定义 LLM
# ==========================
DEFAULT_BASE_URL = "http://127.0.0.1:8000"

class QwenHTTP(LLM):
    _base_url: str = PrivateAttr(default=DEFAULT_BASE_URL)

    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self._base_url = (base_url or os.getenv("SHELL_AGENT_SERVER_URL") or DEFAULT_BASE_URL).rstrip("/")

    @property
    def _llm_type(self) -> str:
        return "qwen_http"

    def _call(self, prompt: str, stop=None) -> str:
        resp = requests.post(
            f"{self._base_url}/generate",
            json={"prompt": prompt, "max_new_tokens": 256},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def generate_command(
        self,
        user_input: str,
        session_id: str,
        target_shell: str,
        max_new_tokens: int = 256,
    ) -> str:
        resp = requests.post(
            f"{self._base_url}/generate",
            json={
                "input": user_input,
                "session_id": session_id,
                "target_shell": target_shell,
                "max_new_tokens": max_new_tokens,
            },
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def clear_memory(self, session_id: str) -> bool:
        resp = requests.post(
            f"{self._base_url}/memory/clear",
            json={"session_id": session_id},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        return bool(payload.get("success", False))

    def get_memory_context(self, session_id: str, query: str = "") -> Dict[str, Any]:
        try:
            resp = requests.post(
                f"{self._base_url}/memory/context",
                json={"session_id": session_id, "query": query},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as exc:
            if "404" in str(exc):
                raise RuntimeError(
                    "服务端未提供 memory/context 接口，请重启 model_server.py 以加载最新代码"
                ) from exc
            raise

    def health_check(self) -> Dict[str, Any]:
        """Call /health and return the server status dict."""
        resp = requests.get(f"{self._base_url}/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_rag_sources(self) -> Dict[str, Any]:
        """Call /rag/sources and return indexed document info."""
        resp = requests.get(f"{self._base_url}/rag/sources", timeout=10)
        resp.raise_for_status()
        return resp.json()

# ==========================
# 辅助函数：加载 Prompt
# ==========================
def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_default_retriever(project_root: Optional[Path] = None) -> Optional[RetrieverProtocol]:
    """Create a retriever from env vars.

    Env vars:
    - SHELL_AGENT_ENABLE_RAG: set to 0/false/no/off to disable local retriever
    - SHELL_AGENT_RAG_DOCS: semicolon-separated file/folder paths
    - SHELL_AGENT_RAG_DB: vector db path (default: data/chroma_db)
    - SHELL_AGENT_RAG_COLLECTION: collection name (default: shell_kb)
    """
    if not _is_truthy(os.getenv("SHELL_AGENT_ENABLE_RAG", "1")):
        return None

    try:
        from memory.vector_retriever import VectorRetriever
    except Exception:
        return None

    root = project_root or Path(__file__).resolve().parent.parent
    db_path = os.getenv("SHELL_AGENT_RAG_DB", str(root / "data" / "chroma_db"))
    collection = os.getenv("SHELL_AGENT_RAG_COLLECTION", "shell_kb")

    retriever = VectorRetriever(persist_dir=db_path, collection_name=collection)

    docs_spec = os.getenv("SHELL_AGENT_RAG_DOCS", "")
    if docs_spec:
        sources = [s.strip() for s in docs_spec.split(";") if s.strip()]
        retriever.build_or_update_index_from_paths(sources)

    return retriever


def generate_with_memory_context(
    llm: QwenHTTP,
    memory: SQLiteMemoryWrapper,
    prompt: PromptTemplate,
    user_input: str,
) -> str:
    """Build prompt from memory once and call model once for each user input."""
    memory_vars = memory.load_memory_variables({"input": user_input})
    model_prompt = prompt.format(
        summary=memory_vars.get("summary", ""),
        recent_history=memory_vars.get("recent_history", ""),
        relevant_memory=memory_vars.get("relevant_memory", ""),
        input=user_input,
    )
    return llm._call(model_prompt)

# ==========================
# 主程序
# ==========================
def main():
    # 初始化 LLM
    llm = QwenHTTP()

    # 初始化 SQLiteMemory
    sqlite_mem = SQLiteMemory(db_path="../data/memory.db")
    retriever = create_default_retriever(Path(__file__).resolve().parent.parent)
    memory = SQLiteMemoryWrapper(sqlite_mem, retriever=retriever)

    # 加载 PromptTemplate
    prompt_text = load_prompt("../prompts/shell_assistant.prompt")
    prompt = PromptTemplate(
        input_variables=["summary", "recent_history", "relevant_memory", "input"],
        template=prompt_text,
    )

    print("Shell assistant ready. Type 'exit' to quit.")
    while True:
        user_input = input("User: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break

        response = generate_with_memory_context(llm, memory, prompt, user_input)

        # 保存到 SQLiteMemory
        memory.save_context({"input": user_input}, {"output": response})

        print(f"Assistant: {response}")
        print("--------------------------------")

if __name__ == "__main__":
    main()
