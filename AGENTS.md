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
  - `shell_agent_client.py`: Client logic, including `SQLiteMemoryWrapper` and `generate_with_memory_context`.
  - `rag_routing.py`: **Shared** RAG category routing logic (`detect_rag_category`). Both client and server import from here — do **not** duplicate keyword rules elsewhere.
- `tests/`: Unit and integration tests.
- `memory/`: Memory management logic (SQLite, Vector DB).
- `prompts/`: Prompt templates.
- `data/`: Runtime data (databases, indices).
- `config/`: Configuration files.

### Key shared utilities

| Symbol | File | Purpose |
|---|---|---|
| `detect_rag_category(text)` | `src/rag_routing.py` | Maps a user query to a RAG category string (`safety` / `tasks` / `patterns` / `examples` / `commands`). Single source of truth. |
| `generate_with_memory_context(llm, memory, prompt, input)` | `src/shell_agent_client.py` | Loads memory context once then calls the model once. Use instead of building a LangChain chain inline. |

## 7. Configuration

- **Environment Variables:** Used for secrets and runtime settings.

  | Variable | Default | Description |
  |---|---|---|
  | `SHELL_AGENT_SERVER_URL` | `http://127.0.0.1:8000` | Model server base URL used by the client. |
  | `SHELL_AGENT_ENABLE_RAG` | `1` | Set to `0` / `false` / `no` / `off` to disable local RAG retrieval. |
  | `SHELL_AGENT_RAG_DB` | `data/chroma_db` | Path to the ChromaDB persistence directory. |
  | `SHELL_AGENT_RAG_COLLECTION` | `shell_kb` | ChromaDB collection name. |
  | `SHELL_AGENT_RAG_DOCS` | *(empty)* | Semicolon-separated file/folder paths to ingest into the index on startup. |
  | `SHELL_AGENT_SESSION_TTL` | `3600` | Seconds of inactivity before a server-side session is evicted. |

- **ConfigFile:** `pyrightconfig.json` for type checking.

## 8. Git Workflow

- **Commits:** Clear, descriptive commit messages.
- **Branching:** Use feature branches for new development.

## 9. Contribution Guidelines

### 1. Think Before Coding
- State assumptions explicitly before implementing. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.

### 2. Simplicity First
- Write the minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that wasn't requested.
- If it could be 50 lines instead of 200, rewrite it.

### 3. Surgical Changes
- Touch only what you must. Clean up only your own mess.
- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Remove imports/variables/functions that **your** changes made unused; leave pre-existing dead code alone.

### 4. Goal-Driven Execution
Define verifiable success criteria before starting. For multi-step tasks write a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

Translate vague goals into testable ones:
- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → ensure tests pass before and after.
