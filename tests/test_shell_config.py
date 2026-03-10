import pytest

from config.shell_config import get_shell_syntax, to_shell_array_index


def test_bash_and_zsh_array_index_base_differs():
    bash = get_shell_syntax("bash")
    zsh = get_shell_syntax("zsh")

    assert bash.array_index_base == 0
    assert zsh.array_index_base == 1


def test_shell_variable_indirect_reference_differs_between_bash_and_zsh():
    bash = get_shell_syntax("bash")
    zsh = get_shell_syntax("zsh")

    assert bash.variable_indirect.format(name="ptr") == "${!ptr}"
    assert zsh.variable_indirect.format(name="ptr") == "${(P)ptr}"


def test_to_shell_array_index_converts_from_logical_zero_based():
    assert to_shell_array_index(0, "bash") == 0
    assert to_shell_array_index(0, "zsh") == 1
    assert to_shell_array_index(2, "zsh") == 3


def test_shell_alias_is_supported():
    assert get_shell_syntax("sh").name == "bash"


def test_unsupported_shell_raises_clear_error():
    with pytest.raises(ValueError) as exc_info:
        get_shell_syntax("fish")

    assert "Unsupported shell" in str(exc_info.value)
