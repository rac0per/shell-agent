import pytest

from src.rag_routing import detect_rag_category


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
def test_detect_rag_category_shared(text: str, expected: str):
    assert detect_rag_category(text) == expected
