from pathlib import Path
import os
import sys
import time
from threading import Lock
from typing import Any, Dict, List, Optional, Protocol

import torch
from flask import Flask, request, jsonify
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from langchain_core.prompts import PromptTemplate

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from memory.sqlite_memory import SQLiteMemory
from src.rag_routing import detect_rag_category


class RagRetriever(Protocol):
    def retrieve(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    def build_or_update_index_from_paths(self, paths: List[str]) -> int:
        ...

    def list_sources(self) -> Dict[str, int]:
        ...

    def list_categories(self) -> Dict[str, int]:
        ...


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

MODEL_PATH = (Path(__file__).resolve().parent.parent / "models" / "qwen-7b").resolve()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "shell_assistant.prompt"
SERVER_MEMORY_DB = PROJECT_ROOT / "data" / "server_memory.db"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model path not found: {MODEL_PATH}")

if not PROMPT_PATH.exists():
    raise FileNotFoundError(f"Prompt path not found: {PROMPT_PATH}")

app = Flask(__name__)

SESSION_MEMORY: Dict[str, SQLiteMemory] = {}
SESSION_LOCK = Lock()
SESSION_LAST_USED: Dict[str, float] = {}
SESSION_TTL_SECONDS = int(os.getenv("SHELL_AGENT_SESSION_TTL", "3600"))  # default 1h
PROMPT_TEXT = PROMPT_PATH.read_text(encoding="utf-8")
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["summary", "recent_history", "relevant_memory", "input", "target_shell"],
    template=PROMPT_TEXT,
)


def _create_rag_retriever() -> Optional[RagRetriever]:
    if not _is_truthy(os.getenv("SHELL_AGENT_ENABLE_RAG", "1")):
        return None

    try:
        from memory.vector_retriever import VectorRetriever
    except Exception:
        return None

    db_path = os.getenv("SHELL_AGENT_RAG_DB", str(PROJECT_ROOT / "data" / "chroma_db"))
    collection = os.getenv("SHELL_AGENT_RAG_COLLECTION", "shell_kb")
    retriever = VectorRetriever(persist_dir=db_path, collection_name=collection)

    docs_spec = os.getenv("SHELL_AGENT_RAG_DOCS", "")
    if docs_spec:
        sources = [s.strip() for s in docs_spec.split(";") if s.strip()]
        retriever.build_or_update_index_from_paths(sources)

    return retriever


RAG_RETRIEVER = _create_rag_retriever()

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    str(MODEL_PATH),
    trust_remote_code=True
)

print("Configuring 4-bit quantization...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
    llm_int8_enable_fp32_cpu_offload=True,
)

print("Loading model (ONLY ONCE)...")
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_PATH),
    quantization_config=bnb_config,
    device_map="balanced",
    max_memory={
        0: "7GB",
        "cpu": "32GB",
    },
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)
model.eval()

print("Model server is ready.")


def _get_session_memory(session_id: str) -> SQLiteMemory:
    with SESSION_LOCK:
        _evict_stale_sessions()
        memory = SESSION_MEMORY.get(session_id)
        if memory is not None:
            SESSION_LAST_USED[session_id] = time.monotonic()
            return memory

        memory = SQLiteMemory(db_path=str(SERVER_MEMORY_DB), session_id=session_id)
        SESSION_MEMORY[session_id] = memory
        SESSION_LAST_USED[session_id] = time.monotonic()
        return memory


def _evict_stale_sessions() -> None:
    """Remove sessions that have been idle longer than SESSION_TTL_SECONDS."""
    now = time.monotonic()
    stale = [
        sid for sid, ts in SESSION_LAST_USED.items()
        if now - ts > SESSION_TTL_SECONDS
    ]
    for sid in stale:
        evicted = SESSION_MEMORY.pop(sid, None)
        if evicted is not None:
            try:
                evicted.conn.close()
            except Exception:
                pass
        SESSION_LAST_USED.pop(sid, None)


def _detect_rag_category(user_input: str) -> Optional[str]:
    """Heuristic: map user query keywords to a doc category for focused retrieval."""
    return detect_rag_category(user_input)


def _build_memory_context(memory: SQLiteMemory, user_input: str) -> Dict[str, str]:
    context = memory.get_memory_context(user_input)

    if RAG_RETRIEVER and user_input.strip():
        category = _detect_rag_category(user_input)
        rag_docs = RAG_RETRIEVER.retrieve(user_input, top_k=4, category_filter=category)
        # If the focused category yields nothing, fall back to unrestricted retrieval
        if not rag_docs:
            rag_docs = RAG_RETRIEVER.retrieve(user_input, top_k=4)
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
                cat = str(doc.get("category", "")).strip()
                score_text = f" score={float(score):.4f}" if isinstance(score, (int, float)) else ""
                category_text = f" category={cat}" if cat else ""
                source_line = f"source={source}{category_text}{score_text}" if source else f"source=unknown{category_text}{score_text}"
                rag_blocks.append(f"<doc {source_line}>\n{content}\n</doc>")

            rag_text = "\n".join(rag_blocks)
            existing = context.get("relevant_memory", "")
            context["relevant_memory"] = (
                f"{existing}\n{rag_text}".strip() if existing else rag_text
            )

    return context


def _generate_response_from_prompt(prompt: str, max_new_tokens: int = 256) -> str:
    messages = [{"role": "user", "content": prompt}]

    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    for attempt in range(2):
        with torch.no_grad():
            if attempt == 0:
                output_ids = model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=0.1,
                    top_p=0.9,
                    do_sample=True,
                )
            else:
                output_ids = model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                )

        decoded = tokenizer.decode(
            output_ids[0][input_ids.shape[-1]:],
            skip_special_tokens=True
        ).strip()

        if decoded:
            return decoded

    # Deterministic final fallback for robustness: never return an empty response.
    return '{"command":"","explanation":"抱歉，刚刚没有生成有效内容。请重试一次，或换一种说法。","warning":""}'

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    prompt = data.get("prompt", "")
    user_input = data.get("input", "")
    session_id = data.get("session_id", "default")
    target_shell = data.get("target_shell", "bash")
    max_new_tokens = min(int(data.get("max_new_tokens", 256)), 2048)

    if prompt:
        response = _generate_response_from_prompt(prompt, max_new_tokens=max_new_tokens)
        return jsonify({
            "response": response
        })

    if not user_input:
        return jsonify({"error": "prompt is required"}), 400

    memory = _get_session_memory(session_id)
    memory_context = _build_memory_context(memory, user_input)
    model_prompt = PROMPT_TEMPLATE.format(
        summary=memory_context.get("summary", ""),
        recent_history=memory_context.get("recent_history", ""),
        relevant_memory=memory_context.get("relevant_memory", ""),
        input=user_input,
        target_shell=target_shell,
    )
    response = _generate_response_from_prompt(model_prompt, max_new_tokens=max_new_tokens)

    memory.add_message("user", user_input)
    memory.add_message("assistant", response)

    return jsonify({
        "response": response,
        "session_id": session_id,
    })


@app.route("/memory/clear", methods=["POST"])
def clear_memory():
    data = request.json or {}
    session_id = data.get("session_id", "")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    memory = _get_session_memory(session_id)
    memory.clear_history()

    return jsonify({
        "success": True,
        "session_id": session_id,
    })


@app.route("/memory/context", methods=["POST"])
def get_memory_context():
    data = request.json or {}
    session_id = data.get("session_id", "")
    query = data.get("query", "")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    memory = _get_session_memory(session_id)
    context = _build_memory_context(memory, query)
    recent_messages = memory.get_recent_history(limit=8)

    return jsonify({
        "session_id": session_id,
        "summary": context.get("summary", ""),
        "recent_history": context.get("recent_history", ""),
        "relevant_memory": context.get("relevant_memory", ""),
        "recent_messages": recent_messages,
    })


@app.route("/health", methods=["GET"])
def health():
    with SESSION_LOCK:
        active_sessions = len(SESSION_MEMORY)
    return jsonify({
        "status": "ok",
        "model": str(MODEL_PATH.name),
        "rag_enabled": RAG_RETRIEVER is not None,
        "active_sessions": active_sessions,
    })


@app.route("/rag/sources", methods=["GET"])
def rag_sources():
    if RAG_RETRIEVER is None:
        return jsonify({"error": "RAG not enabled"}), 503
    sources = RAG_RETRIEVER.list_sources()
    categories = RAG_RETRIEVER.list_categories()
    return jsonify({
        "total_chunks": sum(sources.values()),
        "total_documents": len(sources),
        "categories": categories,
        "sources": sources,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
