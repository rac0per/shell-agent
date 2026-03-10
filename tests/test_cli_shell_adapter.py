from src.cli_interface import ShellAgentCLI


def _make_cli_with_shell(shell_name: str):
    cli = ShellAgentCLI.__new__(ShellAgentCLI)
    cli.target_shell = shell_name
    return cli


def test_adapt_command_bash_to_zsh_common_patterns():
    cli = _make_cli_with_shell("zsh")

    command = 'echo ${!ptr} ${#arr[@]} ${arr[0]}'
    adapted = cli.adapt_command_for_shell(command)

    assert adapted == 'echo ${(P)ptr} ${#arr} ${arr[1]}'


def test_adapt_command_zsh_to_bash_common_patterns():
    cli = _make_cli_with_shell("bash")

    command = 'echo ${(P)ptr} ${#arr} ${arr[1]}'
    adapted = cli.adapt_command_for_shell(command)

    assert adapted == 'echo ${!ptr} ${#arr[@]} ${arr[0]}'


def test_adapt_command_keeps_empty_string():
    cli = _make_cli_with_shell("bash")

    assert cli.adapt_command_for_shell("  ") == ""
