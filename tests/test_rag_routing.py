"""Focused tests for RAG category routing and RAG health APIs in QwenHTTP."""

import pytest

from src.shell_agent_client import QwenHTTP, _detect_rag_category


class _DummyResponse:
    def __init__(self, payload, status_raises=False):
        self._payload = payload
        self._status_raises = status_raises

    def raise_for_status(self):
        if self._status_raises:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


@pytest.mark.parametrize(
    "text,expected",
    [
        ("sudo rm important files", "safety"),
        ("备份文件步骤", "tasks"),
        ("difference between bash and zsh", "patterns"),
        ("show me an example command", "examples"),
        ("list files in current directory", "commands"),
        ("", "commands"),
    ],
)
def test_detect_rag_category(text: str, expected: str):
    assert _detect_rag_category(text) == expected


def test_qwen_http_health_check(monkeypatch):
    llm = QwenHTTP(base_url="http://127.0.0.1:8000")

    def fake_get(url, timeout):
        assert url.endswith("/health")
        assert timeout == 10
        return _DummyResponse({"status": "ok", "rag_enabled": True})

    monkeypatch.setattr("src.shell_agent_client.requests.get", fake_get)

    payload = llm.health_check()
    assert payload["status"] == "ok"
    assert payload["rag_enabled"] is True


def test_qwen_http_health_check_http_error(monkeypatch):
    llm = QwenHTTP(base_url="http://127.0.0.1:8000")

    def fake_get(url, timeout):
        return _DummyResponse({}, status_raises=True)

    monkeypatch.setattr("src.shell_agent_client.requests.get", fake_get)

    with pytest.raises(RuntimeError, match="http error"):
        llm.health_check()


def test_qwen_http_get_rag_sources(monkeypatch):
    llm = QwenHTTP(base_url="http://127.0.0.1:8000")

    expected = {
        "total_chunks": 3,
        "total_documents": 2,
        "categories": {"safety": 2, "commands": 1},
        "sources": {"docs/safety/policy.md": 2, "docs/commands/ls.md": 1},
    }

    def fake_get(url, timeout):
        assert url.endswith("/rag/sources")
        assert timeout == 10
        return _DummyResponse(expected)

    monkeypatch.setattr("src.shell_agent_client.requests.get", fake_get)

    payload = llm.get_rag_sources()
    assert payload == expected


def test_qwen_http_get_rag_sources_http_error(monkeypatch):
    llm = QwenHTTP(base_url="http://127.0.0.1:8000")

    def fake_get(url, timeout):
        return _DummyResponse({}, status_raises=True)

    monkeypatch.setattr("src.shell_agent_client.requests.get", fake_get)

    with pytest.raises(RuntimeError, match="http error"):
        llm.get_rag_sources()
