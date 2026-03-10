from pathlib import Path

import pytest

from src.shell_agent_client import QwenHTTP, load_prompt


class _DummyResponse:
    def __init__(self, payload, status_raises=False):
        self._payload = payload
        self._status_raises = status_raises

    def raise_for_status(self):
        if self._status_raises:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


def test_load_prompt_reads_file(tmp_path):
    prompt_file = tmp_path / "p.prompt"
    prompt_file.write_text("hello {input}", encoding="utf-8")

    text = load_prompt(str(prompt_file))

    assert text == "hello {input}"


def test_qwen_http_call_success(monkeypatch):
    llm = QwenHTTP()

    def fake_post(url, json, timeout):
        assert url.endswith("/generate")
        assert json["prompt"] == "question"
        assert json["max_new_tokens"] == 256
        assert timeout == 300
        return _DummyResponse({"response": "answer"})

    monkeypatch.setattr("src.shell_agent_client.requests.post", fake_post)

    output = llm._call("question")
    assert output == "answer"


def test_qwen_http_call_http_error(monkeypatch):
    llm = QwenHTTP()

    def fake_post(url, json, timeout):
        return _DummyResponse({}, status_raises=True)

    monkeypatch.setattr("src.shell_agent_client.requests.post", fake_post)

    with pytest.raises(RuntimeError, match="http error"):
        llm._call("question")


def test_qwen_http_generate_command_uses_session_payload(monkeypatch):
    llm = QwenHTTP()

    def fake_post(url, json, timeout):
        assert url.endswith("/generate")
        assert json["input"] == "list files"
        assert json["session_id"] == "s1"
        assert json["target_shell"] == "bash"
        assert json["max_new_tokens"] == 64
        assert timeout == 300
        return _DummyResponse({"response": "{\"command\":\"ls\",\"explanation\":\"list\",\"warning\":\"\"}"})

    monkeypatch.setattr("src.shell_agent_client.requests.post", fake_post)

    output = llm.generate_command(
        user_input="list files",
        session_id="s1",
        target_shell="bash",
        max_new_tokens=64,
    )
    assert output.startswith('{"command"')


def test_qwen_http_clear_memory_success(monkeypatch):
    llm = QwenHTTP()

    def fake_post(url, json, timeout):
        assert url.endswith("/memory/clear")
        assert json["session_id"] == "abc"
        assert timeout == 30
        return _DummyResponse({"success": True, "session_id": "abc"})

    monkeypatch.setattr("src.shell_agent_client.requests.post", fake_post)

    assert llm.clear_memory("abc") is True


def test_qwen_http_get_memory_context(monkeypatch):
    llm = QwenHTTP()

    def fake_post(url, json, timeout):
        assert url.endswith("/memory/context")
        assert json["session_id"] == "abc"
        assert json["query"] == ""
        assert timeout == 30
        return _DummyResponse({"session_id": "abc", "summary": "s", "recent_messages": []})

    monkeypatch.setattr("src.shell_agent_client.requests.post", fake_post)

    payload = llm.get_memory_context("abc")
    assert payload["session_id"] == "abc"
    assert payload["summary"] == "s"
