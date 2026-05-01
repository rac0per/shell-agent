"""Tests for VectorRetriever – all chromadb / sentence-transformers deps are mocked."""
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from memory.vector_retriever import VectorRetriever


# ---------------------------------------------------------------------------
# Helpers to build a lightweight VectorRetriever without real ML deps
# ---------------------------------------------------------------------------

def _make_retriever(**kwargs) -> VectorRetriever:
    """Return a VectorRetriever whose __init__ deps are all mocked."""
    mock_chroma_module = MagicMock()
    mock_st_module = MagicMock()

    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_chroma_module.PersistentClient.return_value = mock_client

    mock_embed_model = MagicMock()
    mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])
    mock_st_cls = MagicMock(return_value=mock_embed_model)
    mock_st_module.SentenceTransformer = mock_st_cls

    with patch("importlib.import_module") as mock_import:
        def _side_effect(name):
            if name == "chromadb":
                return mock_chroma_module
            if name == "sentence_transformers":
                return mock_st_module
            raise ImportError(name)
        mock_import.side_effect = _side_effect
        r = VectorRetriever(**kwargs)

    # Expose mocks for assertions
    r._mock_collection = mock_collection  # type: ignore[attr-defined]
    r._mock_embed_model = mock_embed_model  # type: ignore[attr-defined]
    return r


# ---------------------------------------------------------------------------
# _detect_category (classmethod – no instance needed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path_str,expected", [
    ("docs/commands/ls.md", "commands"),
    ("docs/safety/blacklist.md", "safety"),
    ("docs/tasks/backup_sop.md", "tasks"),
    ("docs/patterns/bash_zsh.md", "patterns"),
    ("docs/examples/nl_to_shell.md", "examples"),
    ("docs/SAFETY/policy.md", "safety"),   # case-insensitive
    ("readme.md", "general"),
    ("data/misc.txt", "general"),
])
def test_detect_category(path_str: str, expected: str):
    result = VectorRetriever._detect_category(Path(path_str))
    assert result == expected


# ---------------------------------------------------------------------------
# _chunk_text – markdown-aware splitting
# ---------------------------------------------------------------------------

def test_chunk_text_short_returns_single_chunk():
    r = _make_retriever()
    r.chunk_size = 200
    chunks = r._chunk_text("hello world")
    assert chunks == ["hello world"]


def test_chunk_text_empty_returns_empty():
    r = _make_retriever()
    chunks = r._chunk_text("   ")
    assert chunks == []


def test_chunk_text_splits_on_markdown_headings():
    r = _make_retriever(chunk_size=60, chunk_overlap=10)
    text = (
        "## Section One\n"
        "Short content here.\n\n"
        "## Section Two\n"
        "Other content here."
    )
    chunks = r._chunk_text(text)
    assert len(chunks) >= 2
    # Each chunk should be at most chunk_size characters
    for chunk in chunks:
        assert len(chunk) <= r.chunk_size + 10  # small tolerance for edge joining


def test_chunk_text_falls_back_character_split_for_huge_sections():
    r = _make_retriever(chunk_size=50, chunk_overlap=5)
    # Single paragraph of 200 chars
    text = "A" * 200
    chunks = r._chunk_text(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= r.chunk_size


def test_chunk_text_no_empty_chunks():
    r = _make_retriever(chunk_size=80, chunk_overlap=10)
    text = "\n\n## Title\n\nSome text.\n\n## Another\n\nMore text.\n\n"
    chunks = r._chunk_text(text)
    assert all(c.strip() for c in chunks)


# ---------------------------------------------------------------------------
# retrieve – distance_threshold quality filter
# ---------------------------------------------------------------------------

def _build_query_result(docs, distances, metadatas=None):
    if metadatas is None:
        metadatas = [{"source": f"src_{i}", "chunk_index": i, "category": "commands"} for i in range(len(docs))]
    return {
        "documents": [docs],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def test_retrieve_filters_by_distance_threshold():
    r = _make_retriever(distance_threshold=0.5)
    r._mock_collection.query.return_value = _build_query_result(
        ["close doc", "far doc"],
        [0.2, 0.8],
    )
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("test query", top_k=4)

    assert len(results) == 1
    assert results[0]["content"] == "close doc"


def test_retrieve_all_filtered_when_all_too_far():
    r = _make_retriever(distance_threshold=0.1)
    r._mock_collection.query.return_value = _build_query_result(
        ["doc1", "doc2"],
        [0.5, 0.9],
    )
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("test query", top_k=4)
    assert results == []


# ---------------------------------------------------------------------------
# retrieve – max_chunks_per_source deduplication
# ---------------------------------------------------------------------------

def test_retrieve_limits_chunks_per_source():
    r = _make_retriever(distance_threshold=10.0, max_chunks_per_source=1)
    metas = [
        {"source": "file_a.md", "chunk_index": 0, "category": "commands"},
        {"source": "file_a.md", "chunk_index": 1, "category": "commands"},
        {"source": "file_b.md", "chunk_index": 0, "category": "commands"},
    ]
    r._mock_collection.query.return_value = _build_query_result(
        ["a0", "a1", "b0"], [0.1, 0.2, 0.3], metadatas=metas
    )
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("query", top_k=10)

    sources = [row["source"] for row in results]
    assert sources.count("file_a.md") == 1
    assert sources.count("file_b.md") == 1


def test_retrieve_respects_top_k_after_filtering():
    r = _make_retriever(distance_threshold=10.0, max_chunks_per_source=2)
    docs = [f"doc{i}" for i in range(10)]
    metas = [{"source": f"src_{i}", "chunk_index": 0, "category": "commands"} for i in range(10)]
    r._mock_collection.query.return_value = _build_query_result(
        docs, [0.1 * i for i in range(10)], metadatas=metas
    )
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("query", top_k=3)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# retrieve – category_filter passes where= to chroma
# ---------------------------------------------------------------------------

def test_retrieve_passes_where_filter_when_category_filter_given():
    r = _make_retriever(distance_threshold=10.0)
    r._mock_collection.query.return_value = _build_query_result(["doc"], [0.1])
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    r.retrieve("query", top_k=2, category_filter="safety")

    call_kwargs = r._mock_collection.query.call_args[1]
    assert call_kwargs.get("where") == {"category": "safety"}


def test_retrieve_no_where_filter_when_no_category():
    r = _make_retriever(distance_threshold=10.0)
    r._mock_collection.query.return_value = _build_query_result(["doc"], [0.1])
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    r.retrieve("query", top_k=2)

    call_kwargs = r._mock_collection.query.call_args[1]
    assert "where" not in call_kwargs


def test_retrieve_result_includes_category_field():
    r = _make_retriever(distance_threshold=10.0)
    metas = [{"source": "f.md", "chunk_index": 0, "category": "safety"}]
    r._mock_collection.query.return_value = _build_query_result(["sec doc"], [0.1], metadatas=metas)
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("query")
    assert results[0]["category"] == "safety"


def test_retrieve_hybrid_rescues_keyword_match_when_vector_distance_is_far():
    r = _make_retriever(distance_threshold=0.2, hybrid_enabled=True)

    # Vector retrieval returns a far candidate (would be filtered without keyword signal)
    r._mock_collection.query.return_value = _build_query_result(
        ["use chmod +x deploy.sh"],
        [0.9],
        metadatas=[{"source": "docs/commands/change_permissions_chmod.md", "chunk_index": 0, "category": "commands"}],
    )

    # Keyword retrieval sees the same document and gives it keyword score
    r._mock_collection.count.return_value = 1
    r._mock_collection.get.return_value = {
        "ids": ["doc-1"],
        "documents": ["use chmod +x deploy.sh"],
        "metadatas": [{"source": "docs/commands/change_permissions_chmod.md", "chunk_index": 0, "category": "commands"}],
    }
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("chmod deploy script", top_k=3)
    assert len(results) == 1
    assert "chmod" in str(results[0]["content"]).lower()


def test_retrieve_hybrid_disabled_keeps_original_distance_filter_behavior():
    r = _make_retriever(distance_threshold=0.2, hybrid_enabled=False)
    r._mock_collection.query.return_value = _build_query_result(
        ["use chmod +x deploy.sh"],
        [0.9],
        metadatas=[{"source": "docs/commands/change_permissions_chmod.md", "chunk_index": 0, "category": "commands"}],
    )
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    results = r.retrieve("chmod deploy script", top_k=3)
    assert results == []


def test_retrieve_empty_query_returns_empty():
    r = _make_retriever()
    results = r.retrieve("   ")
    assert results == []
    r._mock_collection.query.assert_not_called()


# ---------------------------------------------------------------------------
# list_sources / list_categories
# ---------------------------------------------------------------------------

def _make_get_result(metadatas):
    return {"metadatas": metadatas, "ids": [str(i) for i in range(len(metadatas))]}


def test_list_sources_returns_chunk_counts():
    r = _make_retriever()
    r._mock_collection.count.return_value = 3
    r._mock_collection.get.return_value = _make_get_result([
        {"source": "a.md", "category": "commands"},
        {"source": "a.md", "category": "commands"},
        {"source": "b.md", "category": "safety"},
    ])

    sources = r.list_sources()
    assert sources == {"a.md": 2, "b.md": 1}


def test_list_sources_empty_collection():
    r = _make_retriever()
    r._mock_collection.count.return_value = 0
    assert r.list_sources() == {}


def test_list_categories_aggregates_correctly():
    r = _make_retriever()
    r._mock_collection.count.return_value = 4
    r._mock_collection.get.return_value = _make_get_result([
        {"source": "a.md", "category": "commands"},
        {"source": "b.md", "category": "safety"},
        {"source": "c.md", "category": "commands"},
        {"source": "d.md", "category": "tasks"},
    ])

    cats = r.list_categories()
    assert cats == {"commands": 2, "safety": 1, "tasks": 1}


# ---------------------------------------------------------------------------
# delete_by_source
# ---------------------------------------------------------------------------

def test_delete_by_source_removes_matching_chunks():
    r = _make_retriever()
    r._mock_collection.get.return_value = {
        "ids": ["id1", "id2"],
        "metadatas": [
            {"source": "a.md", "category": "commands"},
            {"source": "a.md", "category": "commands"},
        ],
    }

    deleted = r.delete_by_source("a.md")
    assert deleted == 2
    r._mock_collection.delete.assert_called_once_with(ids=["id1", "id2"])


def test_delete_by_source_returns_zero_when_not_found():
    r = _make_retriever()
    r._mock_collection.get.return_value = {"ids": [], "metadatas": []}

    deleted = r.delete_by_source("nonexistent.md")
    assert deleted == 0
    r._mock_collection.delete.assert_not_called()


# ---------------------------------------------------------------------------
# build_or_update_index_from_paths – category metadata written
# ---------------------------------------------------------------------------

def test_build_index_writes_category_in_metadata(tmp_path):
    # Create a fake docs/safety/policy.md file
    safety_dir = tmp_path / "docs" / "safety"
    safety_dir.mkdir(parents=True)
    policy_file = safety_dir / "policy.md"
    policy_file.write_text("Do not run rm -rf /", encoding="utf-8")

    r = _make_retriever()
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    count = r.build_or_update_index_from_paths([str(safety_dir)])
    assert count == 1

    call_kwargs = r._mock_collection.upsert.call_args[1]
    assert call_kwargs["metadatas"][0]["category"] == "safety"


def test_build_index_general_category_for_unknown_path(tmp_path):
    misc_file = tmp_path / "notes.md"
    misc_file.write_text("some content", encoding="utf-8")

    r = _make_retriever()
    r._mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 8])

    r.build_or_update_index_from_paths([str(misc_file)])
    call_kwargs = r._mock_collection.upsert.call_args[1]
    assert call_kwargs["metadatas"][0]["category"] == "general"
