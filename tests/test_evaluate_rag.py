from typing import Any, Dict, List

import pytest

from src.evaluate_rag import evaluate


class DummyRetriever:
    def __init__(self, mapping: Dict[str, List[Dict[str, Any]]]):
        self.mapping = mapping

    def retrieve(self, query: str, top_k: int = 4):
        rows = self.mapping.get(query, [])
        return rows[:top_k]


def test_evaluate_reports_mrr_and_ndcg_for_ranked_results():
    query = "chmod command"
    dataset = [
        {
            "query": query,
            "expected_sources": ["docs/commands/change_permissions_chmod.md"],
            "expected_keywords": ["chmod"],
        }
    ]
    retriever = DummyRetriever(
        {
            query: [
                {"source": "docs/safety/file_operation_safety.md", "content": "risk rules"},
                {
                    "source": "docs/commands/change_permissions_chmod.md",
                    "content": "chmod +x deploy.sh",
                },
            ]
        }
    )

    report = evaluate(dataset, retriever, top_k=4)

    assert report["total"] == 1
    assert report["source_hitrate"] == pytest.approx(1.0)
    assert report["keyword_hitrate"] == pytest.approx(1.0)
    assert report["mrr"] == pytest.approx(0.5)
    assert report["ndcg"] == pytest.approx(0.6309297536, rel=1e-6)
    assert report["source_recall_at"]["1"] == pytest.approx(0.0)
    assert report["source_recall_at"]["3"] == pytest.approx(1.0)
    assert report["source_recall_at"]["5"] == pytest.approx(1.0)
    assert report["keyword_recall_at"]["1"] == pytest.approx(0.0)
    assert report["keyword_recall_at"]["3"] == pytest.approx(1.0)
    assert report["keyword_recall_at"]["5"] == pytest.approx(1.0)
    assert report["overall_recall_at"]["1"] == pytest.approx(0.0)
    assert report["overall_recall_at"]["3"] == pytest.approx(1.0)
    assert report["overall_recall_at"]["5"] == pytest.approx(1.0)


def test_evaluate_reports_zero_mrr_and_ndcg_when_no_relevant_doc():
    query = "find logs"
    dataset = [
        {
            "query": query,
            "expected_sources": ["docs/commands/tail_logs_realtime.md"],
            "expected_keywords": ["tail -f"],
        }
    ]
    retriever = DummyRetriever(
        {
            query: [
                {"source": "docs/patterns/query_then_act_pattern.md", "content": "find /tmp"},
                {"source": "docs/safety/file_operation_safety.md", "content": "permission"},
            ]
        }
    )

    report = evaluate(dataset, retriever, top_k=4)

    assert report["source_hitrate"] == pytest.approx(0.0)
    assert report["keyword_hitrate"] == pytest.approx(0.0)
    assert report["mrr"] == pytest.approx(0.0)
    assert report["ndcg"] == pytest.approx(0.0)
    assert report["source_recall_at"]["1"] == pytest.approx(0.0)
    assert report["source_recall_at"]["3"] == pytest.approx(0.0)
    assert report["source_recall_at"]["5"] == pytest.approx(0.0)
    assert report["keyword_recall_at"]["1"] == pytest.approx(0.0)
    assert report["keyword_recall_at"]["3"] == pytest.approx(0.0)
    assert report["keyword_recall_at"]["5"] == pytest.approx(0.0)
    assert report["overall_recall_at"]["1"] == pytest.approx(0.0)
    assert report["overall_recall_at"]["3"] == pytest.approx(0.0)
    assert report["overall_recall_at"]["5"] == pytest.approx(0.0)
