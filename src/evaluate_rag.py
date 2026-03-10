import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.vector_retriever import VectorRetriever


EvalItem = Dict[str, Any]


def _normalize_source_path(text: str) -> str:
    return text.replace("\\", "/").strip().lower()


def _load_dataset(path: Path) -> List[EvalItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Dataset must be a JSON array")
    return payload


def _contains_any(text: str, candidates: List[str]) -> bool:
    text_norm = text.lower()
    for token in candidates:
        if token and token.lower() in text_norm:
            return True
    return False


def evaluate(dataset: List[EvalItem], retriever: VectorRetriever, top_k: int) -> Dict[str, Any]:
    total = 0
    source_hits = 0
    keyword_hits = 0

    details: List[Dict[str, Any]] = []

    for idx, item in enumerate(dataset, start=1):
        query = str(item.get("query", "")).strip()
        if not query:
            continue

        expected_sources = [str(x).strip() for x in item.get("expected_sources", []) if str(x).strip()]
        expected_keywords = [str(x).strip() for x in item.get("expected_keywords", []) if str(x).strip()]

        rows = retriever.retrieve(query, top_k=top_k)
        total += 1

        source_hit = False
        keyword_hit = False

        for row in rows:
            source = str(row.get("source", ""))
            content = str(row.get("content", ""))

            normalized_source = _normalize_source_path(source)
            normalized_expected = [_normalize_source_path(s) for s in expected_sources]
            if expected_sources and _contains_any(normalized_source, normalized_expected):
                source_hit = True
            if expected_keywords and _contains_any(content, expected_keywords):
                keyword_hit = True

        if source_hit:
            source_hits += 1
        if keyword_hit:
            keyword_hits += 1

        details.append(
            {
                "index": idx,
                "query": query,
                "source_hit": source_hit,
                "keyword_hit": keyword_hit,
                "retrieved": rows,
            }
        )

    source_hitrate = (source_hits / total) if total else 0.0
    keyword_hitrate = (keyword_hits / total) if total else 0.0

    return {
        "total": total,
        "top_k": top_k,
        "source_hits": source_hits,
        "source_hitrate": source_hitrate,
        "keyword_hits": keyword_hits,
        "keyword_hitrate": keyword_hitrate,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local RAG retrieval quality")
    parser.add_argument("--dataset", default="data/rag_eval_set.template.json", help="Evaluation dataset JSON path")
    parser.add_argument("--db", default="data/chroma_db", help="Vector DB directory")
    parser.add_argument("--collection", default="shell_kb", help="Collection name")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="SentenceTransformer model")
    parser.add_argument("--top-k", type=int, default=4, help="Top-k documents to retrieve")
    parser.add_argument("--output", default="", help="Optional output report JSON path")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset = _load_dataset(dataset_path)
    retriever = VectorRetriever(
        persist_dir=args.db,
        collection_name=args.collection,
        embedding_model=args.model,
    )

    report = evaluate(dataset, retriever, top_k=args.top_k)

    print(f"Total queries: {report['total']}")
    print(f"Top-k: {report['top_k']}")
    print(f"Source HitRate@{report['top_k']}: {report['source_hitrate']:.4f} ({report['source_hits']}/{report['total']})")
    print(f"Keyword HitRate@{report['top_k']}: {report['keyword_hitrate']:.4f} ({report['keyword_hits']}/{report['total']})")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved report to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
