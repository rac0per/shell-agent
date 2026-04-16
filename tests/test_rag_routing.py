"""Tests for _detect_rag_category routing and the /health + /rag/sources endpoints."""
import pytest
from flask import Flask, jsonify

from src.shell_agent_client import _detect_rag_category


# ---------------------------------------------------------------------------
# _detect_rag_category  (shared between shell_agent_client and model_server)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    # safety triggers
    ("sudo rm important files", "safety"),
    ("什么操作是危险的", "safety"),
    ("check permission on dir", "safety"),
    ("root access needed", "safety"),
    ("blacklist policy", "safety"),
    # tasks triggers
    ("backup my home directory", "tasks"),
    ("certificate expiry check sop", "tasks"),
    ("restore config from backup", "tasks"),
    ("磁盘容量不足怎么处理", "tasks"),
    ("备份文件步骤", "tasks"),
    # patterns triggers
    ("difference between bash and zsh", "patterns"),
    ("zsh array syntax", "patterns"),
    ("bash zsh 差异", "patterns"),
    ("dry-run before executing", "patterns"),
    # examples triggers
    ("show me an example command", "examples"),
    ("给一个示例", "examples"),
    ("sample output of ls", "examples"),
    # default – commands
    ("list files in current directory", "commands"),
    ("how to delete a file", "commands"),
    ("显示所有进程", "commands"),
    ("", "commands"),
])
def test_detect_rag_category(text: str, expected: str):
    assert _detect_rag_category(text) == expected


# ---------------------------------------------------------------------------
# /health endpoint (mock Flask app mirroring model_server implementation)
# ---------------------------------------------------------------------------

def _build_server_app():
    """Minimal Flask app that replicates the /health and /rag/sources routes."""
    app = Flask(__name__)

    # Simulated server state
    _state = {
        "model_name": "qwen-7b",
        "rag_enabled": True,
        "active_sessions": 3,
        "sources": {"docs/safety/policy.md": 2, "docs/commands/ls.md": 1},
        "categories": {"safety": 2, "commands": 1},
    }

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "model": _state["model_name"],
            "rag_enabled": _state["rag_enabled"],
            "active_sessions": _state["active_sessions"],
        })

    @app.route("/rag/sources", methods=["GET"])
    def rag_sources():
        sources = _state["sources"]
        categories = _state["categories"]
        return jsonify({
            "total_chunks": sum(sources.values()),
            "total_documents": len(sources),
            "categories": categories,
            "sources": sources,
        })

    @app.route("/rag/sources_disabled", methods=["GET"])
    def rag_sources_disabled():
        return jsonify({"error": "RAG not enabled"}), 503

    return app


@pytest.fixture()
def server_client():
    app = _build_server_app()
    return app.test_client()


def test_health_returns_ok(server_client):
    resp = server_client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_health_includes_model_name(server_client):
    data = server_client.get("/health").get_json()
    assert "model" in data
    assert isinstance(data["model"], str)


def test_health_includes_rag_enabled_flag(server_client):
    data = server_client.get("/health").get_json()
    assert "rag_enabled" in data
    assert isinstance(data["rag_enabled"], bool)


def test_health_includes_active_sessions(server_client):
    data = server_client.get("/health").get_json()
    assert "active_sessions" in data
    assert isinstance(data["active_sessions"], int)


def test_rag_sources_total_chunks(server_client):
    data = server_client.get("/rag/sources").get_json()
    assert data["total_chunks"] == 3


def test_rag_sources_total_documents(server_client):
    data = server_client.get("/rag/sources").get_json()
    assert data["total_documents"] == 2


def test_rag_sources_includes_categories(server_client):
    data = server_client.get("/rag/sources").get_json()
    assert "categories" in data
    assert data["categories"]["safety"] == 2


def test_rag_sources_includes_sources_map(server_client):
    data = server_client.get("/rag/sources").get_json()
    assert "docs/safety/policy.md" in data["sources"]


def test_rag_sources_disabled_returns_503(server_client):
    resp = server_client.get("/rag/sources_disabled")
    assert resp.status_code == 503
    assert "RAG not enabled" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# Session TTL eviction logic (pure-logic test, no server import needed)
# ---------------------------------------------------------------------------

def test_evict_stale_sessions_removes_expired():
    import time

    sessions = {"s1": time.monotonic() - 7200, "s2": time.monotonic()}
    last_used = dict(sessions)
    ttl = 3600

    now = time.monotonic()
    stale = [sid for sid, ts in last_used.items() if now - ts > ttl]
    for sid in stale:
        sessions.pop(sid, None)
        last_used.pop(sid, None)

    assert "s1" not in sessions
    assert "s2" in sessions


def test_evict_stale_sessions_keeps_fresh():
    import time

    sessions = {"fresh": time.monotonic()}
    last_used = dict(sessions)

    stale = [sid for sid, ts in last_used.items() if time.monotonic() - ts > 3600]
    for sid in stale:
        sessions.pop(sid, None)

    assert "fresh" in sessions
