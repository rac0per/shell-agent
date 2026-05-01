import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.vector_retriever import VectorRetriever
from src.evaluate_rag import evaluate
from src.rag_routing import detect_rag_category


EvalItem = Dict[str, Any]
EvalReport = Dict[str, Any]


def _load_dataset(path: Path) -> List[EvalItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Dataset must be a JSON array")
    return payload


def _run_eval(
    dataset: List[EvalItem],
    *,
    db: str,
    collection: str,
    model: str,
    top_k: int,
    hybrid_enabled: bool,
) -> EvalReport:
    retriever = VectorRetriever(
        persist_dir=db,
        collection_name=collection,
        embedding_model=model,
        hybrid_enabled=hybrid_enabled,
    )
    started_at = time.perf_counter()
    report = evaluate(dataset, retriever, top_k=top_k)
    elapsed_sec = time.perf_counter() - started_at
    report["elapsed_sec"] = elapsed_sec
    report["mode"] = "hybrid" if hybrid_enabled else "vector_only"
    return report


def _as_pct(v: Any) -> str:
    if not isinstance(v, (int, float)):
        return "n/a"
    return f"{float(v):.4f}"


def _print_comparison_table(vector_report: EvalReport, hybrid_report: EvalReport) -> None:
    rows = [
        ("Source HitRate", vector_report.get("source_hitrate"), hybrid_report.get("source_hitrate")),
        ("Keyword HitRate", vector_report.get("keyword_hitrate"), hybrid_report.get("keyword_hitrate")),
        ("MRR", vector_report.get("mrr"), hybrid_report.get("mrr")),
        ("nDCG", vector_report.get("ndcg"), hybrid_report.get("ndcg")),
        ("Source Recall@1", (vector_report.get("source_recall_at") or {}).get("1"), (hybrid_report.get("source_recall_at") or {}).get("1")),
        ("Source Recall@3", (vector_report.get("source_recall_at") or {}).get("3"), (hybrid_report.get("source_recall_at") or {}).get("3")),
        ("Source Recall@5", (vector_report.get("source_recall_at") or {}).get("5"), (hybrid_report.get("source_recall_at") or {}).get("5")),
        ("Elapsed (sec)", vector_report.get("elapsed_sec"), hybrid_report.get("elapsed_sec")),
    ]

    print("\nA/B Comparison")
    print("-" * 84)
    print(f"{'Metric':<22} {'A: Vector-Only':>20} {'B: Hybrid+Rerank':>20} {'Delta(B-A)':>18}")
    print("-" * 84)
    for metric, a_val, b_val in rows:
        delta = None
        if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
            delta = float(b_val) - float(a_val)
        delta_text = f"{delta:+.4f}" if isinstance(delta, float) else "n/a"
        print(f"{metric:<22} {_as_pct(a_val):>20} {_as_pct(b_val):>20} {delta_text:>18}")
    print("-" * 84)


def _classify_failure_reason(
    item: EvalItem,
    detail: Dict[str, Any],
    *,
    is_hybrid: bool,
    vector_detail_for_same_query: Optional[Dict[str, Any]] = None,
) -> str:
    query = str(item.get("query", ""))
    expected_sources = [str(x).lower() for x in item.get("expected_sources", []) if str(x).strip()]
    expected_keywords = [str(x).lower() for x in item.get("expected_keywords", []) if str(x).strip()]

    retrieved = detail.get("retrieved") or []
    if not isinstance(retrieved, list):
        retrieved = []

    if is_hybrid and vector_detail_for_same_query:
        vector_source_hit = bool(vector_detail_for_same_query.get("source_hit", False))
        hybrid_source_hit = bool(detail.get("source_hit", False))
        if vector_source_hit and not hybrid_source_hit:
            return "重排误伤"

    routed_category = detect_rag_category(query) or "commands"
    retrieved_categories = [str(row.get("category", "")) for row in retrieved if isinstance(row, dict)]
    if retrieved_categories and all(cat and cat != routed_category for cat in retrieved_categories):
        return "跨类误召回"

    retrieved_text = "\n".join(
        f"{str(row.get('source', '')).lower()}\n{str(row.get('content', '')).lower()}"
        for row in retrieved
        if isinstance(row, dict)
    )
    has_expected_source = any(src and src in retrieved_text for src in expected_sources)
    has_expected_keyword = any(kw and kw in retrieved_text for kw in expected_keywords)

    if has_expected_source and not has_expected_keyword:
        return "文档粒度不合适"

    return "同义词丢失"


def _extract_failures(
    dataset: List[EvalItem],
    report: EvalReport,
    *,
    count: int,
    is_hybrid: bool,
    vector_report: Optional[EvalReport] = None,
) -> List[Dict[str, Any]]:
    details = report.get("details") or []
    if not isinstance(details, list):
        return []

    vector_by_index: Dict[int, Dict[str, Any]] = {}
    if vector_report:
        for d in (vector_report.get("details") or []):
            if isinstance(d, dict) and isinstance(d.get("index"), int):
                vector_by_index[d["index"]] = d

    failures: List[Dict[str, Any]] = []
    for detail in details:
        if not isinstance(detail, dict):
            continue

        # Failure criterion: either source or keyword target is not met.
        if bool(detail.get("source_hit", False)) and bool(detail.get("keyword_hit", False)):
            continue

        idx = detail.get("index")
        if not isinstance(idx, int) or idx < 1 or idx > len(dataset):
            continue

        item = dataset[idx - 1]
        reason = _classify_failure_reason(
            item,
            detail,
            is_hybrid=is_hybrid,
            vector_detail_for_same_query=vector_by_index.get(idx),
        )

        failures.append(
            {
                "index": idx,
                "query": item.get("query", ""),
                "source_hit": bool(detail.get("source_hit", False)),
                "keyword_hit": bool(detail.get("keyword_hit", False)),
                "reason": reason,
                "top_retrieved": (detail.get("retrieved") or [])[:3],
            }
        )

        if len(failures) >= count:
            break

    return failures


def _print_failure_summary(name: str, failures: List[Dict[str, Any]]) -> None:
    reason_counts = Counter(str(item.get("reason", "未知")) for item in failures)
    print(f"\n{name} Failure Summary (Top {len(failures)})")
    print("-" * 84)
    for reason, cnt in reason_counts.items():
        print(f"- {reason}: {cnt}")

def _print_failure_examples(name: str, failures: List[Dict[str, Any]]) -> None:
    print(f"\n{name} Failure Examples")
    print("-" * 84)
    for item in failures:
        idx = item.get("index")
        query = str(item.get("query", "")).strip()
        reason = str(item.get("reason", ""))
        print(f"[{idx}] {reason} | {query}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run strict A/B evaluation for vector-only vs hybrid retrieval")
    parser.add_argument("--dataset", default="data/rag_eval_docs_only_100.json", help="Evaluation dataset JSON path")
    parser.add_argument("--db", default="data/chroma_db", help="Vector DB directory")
    parser.add_argument("--collection", default="shell_kb", help="Collection name")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="SentenceTransformer model")
    parser.add_argument("--top-k", type=int, default=5, help="Top-k to evaluate")
    parser.add_argument("--failure-count", type=int, default=10, help="How many failures to extract for each arm")
    parser.add_argument("--output", default="", help="Optional output JSON file path")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    dataset = _load_dataset(dataset_path)

    vector_report = _run_eval(
        dataset,
        db=args.db,
        collection=args.collection,
        model=args.model,
        top_k=args.top_k,
        hybrid_enabled=False,
    )
    hybrid_report = _run_eval(
        dataset,
        db=args.db,
        collection=args.collection,
        model=args.model,
        top_k=args.top_k,
        hybrid_enabled=True,
    )

    _print_comparison_table(vector_report, hybrid_report)

    vector_failures = _extract_failures(
        dataset,
        vector_report,
        count=args.failure_count,
        is_hybrid=False,
    )
    hybrid_failures = _extract_failures(
        dataset,
        hybrid_report,
        count=args.failure_count,
        is_hybrid=True,
        vector_report=vector_report,
    )

    _print_failure_summary("A (Vector-Only)", vector_failures)
    _print_failure_summary("B (Hybrid+Rerank)", hybrid_failures)
    _print_failure_examples("A (Vector-Only)", vector_failures)
    _print_failure_examples("B (Hybrid+Rerank)", hybrid_failures)

    output_payload = {
        "dataset": str(dataset_path),
        "top_k": args.top_k,
        "arms": {
            "A_vector_only": vector_report,
            "B_hybrid_rerank": hybrid_report,
        },
        "failure_samples": {
            "A_vector_only": vector_failures,
            "B_hybrid_rerank": hybrid_failures,
        },
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved A/B report to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
