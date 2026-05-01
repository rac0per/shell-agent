from pathlib import Path

from langchain_core.prompts import PromptTemplate


def test_prompt_template_loads_and_has_expected_variables():
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "shell_assistant.prompt"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    prompt = PromptTemplate.from_template(prompt_text)

    assert set(prompt.input_variables) == {
        "summary",
        "recent_history",
        "relevant_memory",
        "input",
    }


def test_prompt_template_can_format_with_all_variables():
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "shell_assistant.prompt"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    prompt = PromptTemplate.from_template(prompt_text)

    rendered = prompt.format(
        summary="s",
        recent_history="h",
        relevant_memory="r",
        input="show files",
    )

    assert "User request:" in rendered
    assert "show files" in rendered


def test_prompt_explicitly_supports_non_command_conversation():
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "shell_assistant.prompt"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert "greeting/chit-chat/general Q&A" in prompt_text
    assert 'set "command" to ""' in prompt_text


def test_prompt_contains_greeting_json_example():
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "shell_assistant.prompt"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert "Greeting example:" in prompt_text
    assert '"command":""' in prompt_text
