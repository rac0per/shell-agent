from dataclasses import dataclass


@dataclass(frozen=True)
class ShellSyntax:
    """Syntax templates for shell-specific command generation."""

    name: str
    array_declare: str
    array_append: str
    array_item: str
    array_all: str
    array_length: str
    variable_ref: str
    variable_default: str
    variable_indirect: str
    array_index_base: int


SHELL_SYNTAX_MAP = {
    "bash": ShellSyntax(
        name="bash",
        array_declare='{name}=({values})',
        array_append='{name}+=("{value}")',
        array_item='${{{name}[{index}]}}',
        array_all='${{{name}[@]}}',
        array_length='${{#{name}[@]}}',
        variable_ref='${{{name}}}',
        variable_default='${{{name}:-{default}}}',
        variable_indirect='${{!{name}}}',
        array_index_base=0,
    ),
    "zsh": ShellSyntax(
        name="zsh",
        array_declare='{name}=({values})',
        array_append='{name}+=("{value}")',
        array_item='${{{name}[{index}]}}',
        array_all='${{{name}[@]}}',
        array_length='${{#{name}}}',
        variable_ref='${{{name}}}',
        variable_default='${{{name}:-{default}}}',
        variable_indirect='${{(P){name}}}',
        array_index_base=1,
    ),
}


def normalize_shell_name(shell_name: str) -> str:
    """Normalize a user-provided shell identifier."""
    if not shell_name:
        raise ValueError("shell_name is required")

    normalized = shell_name.strip().lower()
    aliases = {
        "sh": "bash",
        "gnu bash": "bash",
        "z shell": "zsh",
    }
    return aliases.get(normalized, normalized)


def get_shell_syntax(shell_name: str) -> ShellSyntax:
    """Return shell syntax templates for supported shells."""
    normalized = normalize_shell_name(shell_name)
    if normalized not in SHELL_SYNTAX_MAP:
        supported = ", ".join(sorted(SHELL_SYNTAX_MAP))
        raise ValueError(
            f"Unsupported shell: {shell_name}. Supported shells: {supported}"
        )
    return SHELL_SYNTAX_MAP[normalized]


def to_shell_array_index(index: int, shell_name: str) -> int:
    """Convert a 0-based logical index to a shell-specific array index."""
    if index < 0:
        raise ValueError("index must be >= 0")

    syntax = get_shell_syntax(shell_name)
    return index + syntax.array_index_base
