import argparse
import json
import math
import os
import sys
import time
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


def _relevance_gain(row: Dict[str, Any], expected_sources: List[str], expected_keywords: List[str]) -> int:
    """Return a simple graded relevance score for one retrieved row.

    Gain design:
    - +2 if source matches expected source hints
    - +1 if content matches expected keywords
    """
    source = str(row.get("source", ""))
    content = str(row.get("content", ""))

    source_gain = 0
    keyword_gain = 0

    if expected_sources:
        normalized_source = _normalize_source_path(source)
        normalized_expected = [_normalize_source_path(s) for s in expected_sources]
        if _contains_any(normalized_source, normalized_expected):
            source_gain = 2

    if expected_keywords and _contains_any(content, expected_keywords):
        keyword_gain = 1

    return source_gain + keyword_gain


def _dcg(gains: List[int]) -> float:
    score = 0.0
    for rank, gain in enumerate(gains, start=1):
        if gain <= 0:
            continue
        score += (2**gain - 1) / math.log2(rank + 1)
    return score


def evaluate(dataset: List[EvalItem], retriever: VectorRetriever, top_k: int) -> Dict[str, Any]:
    total = 0
    source_hits = 0
    keyword_hits = 0
    reciprocal_rank_sum = 0.0
    ndcg_sum = 0.0
    source_recall_hits = {1: 0, 3: 0, 5: 0}
    keyword_recall_hits = {1: 0, 3: 0, 5: 0}
    overall_recall_hits = {1: 0, 3: 0, 5: 0}

    details: List[Dict[str, Any]] = []
    retrieve_top_k = max(top_k, 5)

    for idx, item in enumerate(dataset, start=1):
        query = str(item.get("query", "")).strip()
        if not query:
            continue

        expected_sources = [str(x).strip() for x in item.get("expected_sources", []) if str(x).strip()]
        expected_keywords = [str(x).strip() for x in item.get("expected_keywords", []) if str(x).strip()]

        rows = retriever.retrieve(query, top_k=retrieve_top_k)
        total += 1

        source_hit = False
        keyword_hit = False
        gains: List[int] = []
        reciprocal_rank = 0.0

        source_hit_ranks: List[int] = []
        keyword_hit_ranks: List[int] = []

        for rank, row in enumerate(rows, start=1):
            gain = _relevance_gain(row, expected_sources, expected_keywords)
            gains.append(gain)

            if gain > 0 and reciprocal_rank == 0.0:
                reciprocal_rank = 1.0 / rank

            if gain >= 2:
                source_hit = True
                source_hit_ranks.append(rank)
            if gain % 2 == 1:
                keyword_hit = True
                keyword_hit_ranks.append(rank)

        if source_hit:
            source_hits += 1
        if keyword_hit:
            keyword_hits += 1

        for k in (1, 3, 5):
            source_topk_hit = any(r <= k for r in source_hit_ranks)
            keyword_topk_hit = any(r <= k for r in keyword_hit_ranks)
            if source_topk_hit:
                source_recall_hits[k] += 1
            if keyword_topk_hit:
                keyword_recall_hits[k] += 1
            if source_topk_hit or keyword_topk_hit:
                overall_recall_hits[k] += 1

        reciprocal_rank_sum += reciprocal_rank

        dcg_val = _dcg(gains)
        idcg_val = _dcg(sorted(gains, reverse=True))
        ndcg = (dcg_val / idcg_val) if idcg_val > 0 else 0.0
        ndcg_sum += ndcg

        details.append(
            {
                "index": idx,
                "query": query,
                "source_hit": source_hit,
                "keyword_hit": keyword_hit,
                "reciprocal_rank": reciprocal_rank,
                "ndcg": ndcg,
                "retrieved": rows[:top_k],
            }
        )

    source_hitrate = (source_hits / total) if total else 0.0
    keyword_hitrate = (keyword_hits / total) if total else 0.0
    mrr = (reciprocal_rank_sum / total) if total else 0.0
    mean_ndcg = (ndcg_sum / total) if total else 0.0
    source_recall_at = {
        str(k): (source_recall_hits[k] / total) if total else 0.0
        for k in (1, 3, 5)
    }
    keyword_recall_at = {
        str(k): (keyword_recall_hits[k] / total) if total else 0.0
        for k in (1, 3, 5)
    }
    overall_recall_at = {
        str(k): (overall_recall_hits[k] / total) if total else 0.0
        for k in (1, 3, 5)
    }

    return {
        "total": total,
        "top_k": top_k,
        "retrieved_top_k": retrieve_top_k,
        "source_hits": source_hits,
        "source_hitrate": source_hitrate,
        "keyword_hits": keyword_hits,
        "keyword_hitrate": keyword_hitrate,
        "mrr": mrr,
        "ndcg": mean_ndcg,
        "source_recall_at": source_recall_at,
        "keyword_recall_at": keyword_recall_at,
        "overall_recall_at": overall_recall_at,
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

    started_at = time.perf_counter()
    report = evaluate(dataset, retriever, top_k=args.top_k)
    elapsed_sec = time.perf_counter() - started_at
    report["elapsed_sec"] = elapsed_sec

    print(f"Total queries: {report['total']}")
    print(f"Top-k: {report['top_k']}")
    print(f"Retrieved Top-k (internal): {report['retrieved_top_k']}")
    print(f"Source HitRate@{report['top_k']}: {report['source_hitrate']:.4f} ({report['source_hits']}/{report['total']})")
    print(f"Keyword HitRate@{report['top_k']}: {report['keyword_hitrate']:.4f} ({report['keyword_hits']}/{report['total']})")
    print(
        f"Source Recall@1/3/5: "
        f"{report['source_recall_at']['1']:.4f} / "
        f"{report['source_recall_at']['3']:.4f} / "
        f"{report['source_recall_at']['5']:.4f}"
    )
    print(
        f"Keyword Recall@1/3/5: "
        f"{report['keyword_recall_at']['1']:.4f} / "
        f"{report['keyword_recall_at']['3']:.4f} / "
        f"{report['keyword_recall_at']['5']:.4f}"
    )
    print(
        f"Overall Recall@1/3/5: "
        f"{report['overall_recall_at']['1']:.4f} / "
        f"{report['overall_recall_at']['3']:.4f} / "
        f"{report['overall_recall_at']['5']:.4f}"
    )
    print(f"MRR@{report['top_k']}: {report['mrr']:.4f}")
    print(f"nDCG@{report['top_k']}: {report['ndcg']:.4f}")
    print(f"Elapsed: {elapsed_sec:.3f}s")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved report to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
