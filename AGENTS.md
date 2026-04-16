# Shell Agent - Developer Guide

This repository contains a local LLM-based Shell Agent. It consists of a Flask model server and a Rich-based CLI client.

## 1. Environment & Setup

- **Python Version:** 3.10+
- **Virtual Environment:** Recommended.
- **Dependencies:**
  ```bash
  pip install -r requirements.txt
  ```
- **Key Libraries:** `torch`, `transformers`, `flask`, `rich`, `langchain`, `chromadb`.

## 2. Running the Application

The application is split into a server and a client.

### Model Server
Responsible for LLM inference, memory management, and RAG.
```bash
python src/model_server.py
```
*Ensure `models/qwen-7b` (or configured model) exists.*

### CLI Client
The user interface for interacting with the agent.
```bash
python src/cli_interface.py
```
*Optional: Specify shell*
```bash
python src/cli_interface.py --shell zsh
```

## 3. Testing

We use `pytest` for testing.

### Run All Tests
```bash
pytest -q
```

### Run a Single Test File
```bash
pytest tests/test_cli_parsing.py
```

### Run a Single Test Case
```bash
pytest tests/test_cli_parsing.py::test_parse_response_plain_json
```

### Test Structure
- Tests are located in `tests/`.
- Test files should be named `test_*.py`.
- Test functions should be named `test_*`.
- Use `conftest.py` for shared fixtures.

## 4. Linting & Type Checking

- **Type Checking:** The project uses `pyright`. Configuration is in `pyrightconfig.json`.
  - Mode: `basic`
  - Run: `pyright` (requires pyright installed)
- **Formatting:** Follow PEP 8 guidelines.
  - Indentation: 4 spaces.
  - Line length: Keep reasonable (e.g., 88 or 100 chars).

## 5. Code Style & Conventions

### General
- **Language:**
  - Code (variable names, comments, commit messages): English.
  - User Interface / Output: **Chinese** (Simplified).
- **Path Handling:** Use `pathlib.Path` instead of `os.path` where possible for robust cross-platform path manipulation.
  ```python
  from pathlib import Path
  chat_store = Path(__file__).resolve().parent / "data" / "chats.json"
  ```

### Naming
- **Variables & Functions:** `snake_case`
  ```python
  def parse_response(response_text: str) -> dict:
      user_command = ...
  ```
- **Classes:** `CamelCase`
  ```python
  class ShellAgentCLI:
      ...
  ```
- **Constants:** `UPPER_CASE`
  ```python
  DEFAULT_MODEL_PATH = "models/qwen-7b"
  ```
- **Private Members:** `_snake_case` (prefix with `_`)
  ```python
  def _load_chat_state(self):
      ...
  ```

### Type Hinting
- Use Python type hints for function arguments and return values.
- Use `typing` module (or standard collections in 3.9+) for complex types.
  ```python
  from typing import List, Dict, Optional

  def process_items(items: List[str]) -> Dict[str, int]:
      ...
  ```

### Imports
- Group imports:
  1. Standard Library (`import sys`, `import json`)
  2. Third-Party Libraries (`from rich.console import Console`)
  3. Local Application Imports (`from config.shell_config import ...`)
- Avoid `from module import *`.
- Handle relative imports carefully; the project uses `sys.path` modification in entry points to support running scripts directly.

### Error Handling
- Use specific `try/except` blocks.
- Fail gracefully in the CLI; do not crash the application for recoverable errors (e.g., malformed model response).
  ```python
  try:
      payload = json.loads(text)
  except json.JSONDecodeError:
      # Handle error, maybe retry or return raw text
      ...
  ```

### Logging & Output
- Use `rich` for CLI output to provide a better UX (tables, colors, panels).
- Use standard `logging` for server-side logs.

## 6. Project Structure

- `src/`: Source code.
  - `cli_interface.py`: Main CLI entry point.
  - `model_server.py`: Main Server entry point.
  - `shell_agent_client.py`: Client logic.
- `tests/`: Unit and integration tests.
- `memory/`: Memory management logic (SQLite, Vector DB).
- `prompts/`: Prompt templates.
- `data/`: Runtime data (databases, indices).
- `config/`: Configuration files.

## 7. Configuration

- **Environment Variables:** Used for secrets and runtime settings (e.g., `SHELL_AGENT_SERVER_URL`, `SHELL_AGENT_ENABLE_RAG`).
- **ConfigFile:** `pyrightconfig.json` for type checking.

## 8. Git Workflow

- **Commits:** Clear, descriptive commit messages.
- **Branching:** Use feature branches for new development.
