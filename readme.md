# 基于 LLM 的 Shell Agent

一个本地可运行的 Shell 智能助手：
- 支持自然语言转 Shell 命令。
- 支持 Bash / Zsh 语法适配。
- 支持会话隔离、历史记忆与记忆查看。
- 支持可选 RAG 检索增强（基于本地向量库）。
- 支持基础危险命令拦截与执行前确认。

## 项目结构

- `src/cli_interface.py`：命令行前端（Rich UI、会话管理、交互执行）。
- `src/model_server.py`：模型服务（Flask + 模型推理 + 记忆 + 可选 RAG）。
- `src/shell_agent_client.py`：CLI 与服务端通信客户端。
- `src/build_rag_index.py`：离线构建 / 更新向量索引。
- `memory/sqlite_memory.py`：会话记忆存储。
- `memory/vector_retriever.py`：向量检索器。
- `prompts/shell_assistant.prompt`：提示词模板。

## 环境要求

- Python 3.10+（建议）。
- 本地模型目录存在：`models/qwen-7b`。
- 建议具备 GPU；项目默认使用 4-bit 量化加载模型。

安装依赖：

```bash
pip install -r requirements.txt
```

## 快速开始

当前架构是前后端分离：
- CLI 负责输入输出和渲染。
- model_server 负责推理、记忆和 RAG。

1. 启动模型服务

```bash
python src/model_server.py
```

2. 启动 CLI（默认 bash）

```bash
python src/cli_interface.py
```

3. 如需指定目标 Shell（bash/zsh）

```bash
python src/cli_interface.py --shell zsh
```

## CLI 内置命令

- `new [标题]`：新建会话并切换。
- `chats`：查看会话列表。
- `use <序号|标题|session_id>`：切换会话。
- `session`：查看当前会话信息。
- `memory`：查看当前会话记忆上下文。
- `clear`：清空当前会话在服务端的记忆。
- `step <任务>` / `分步 <任务>`：分步生成并逐步确认执行。
- `exit` / `quit`：退出。

说明：普通对话模式下，模型返回命令后仍会二次确认是否执行。

## RAG 检索增强（可选）

默认开启。服务端会把检索结果注入到提示词上下文中。
如需关闭，可设置：`$env:SHELL_AGENT_ENABLE_RAG='0'`。

1. 构建索引（示例）

```bash
python src/build_rag_index.py --source docs --source readme.md
```

2. 设置环境变量（PowerShell 示例）

```powershell
$env:SHELL_AGENT_ENABLE_RAG='1'
$env:SHELL_AGENT_RAG_DOCS='K:\PROJECTS\shell_agent\docs;K:\PROJECTS\shell_agent\readme.md'
$env:SHELL_AGENT_RAG_DB='K:\PROJECTS\shell_agent\data\chroma_db'
$env:SHELL_AGENT_RAG_COLLECTION='shell_kb'
```

3. 重新启动服务端与 CLI

```bash
python src/model_server.py
python src/cli_interface.py
```

## 关键环境变量

- `SHELL_AGENT_SERVER_URL`：CLI 访问的服务地址，默认 `http://127.0.0.1:8000`。
- `SHELL_AGENT_CHAT_STORE`：CLI 会话列表持久化路径。
- `SHELL_AGENT_SESSION_ID`：可选，自定义会话 ID（仅首次会话使用）。
- `SHELL_AGENT_ENABLE_RAG`：是否开启 RAG（`1/true/yes/on`）。
- `SHELL_AGENT_RAG_DOCS`：RAG 数据源，多个路径用分号分隔。
- `SHELL_AGENT_RAG_DB`：向量库目录。
- `SHELL_AGENT_RAG_COLLECTION`：向量集合名。

## 安全说明

CLI 内置了基础高危命令拦截（如 `rm -rf /`、`mkfs`、`shutdown` 等）。
即使通过了拦截，命令执行前仍建议人工确认命令含义和影响范围。

## 测试

```bash
pytest -q
```

## 常见问题

1. 服务端无法启动
- 检查 `models/qwen-7b` 是否存在。
- 检查 CUDA / bitsandbytes / torch 环境是否匹配。

2. CLI 提示连接失败
- 确认 `src/model_server.py` 已启动。
- 确认 `SHELL_AGENT_SERVER_URL` 与服务端地址一致。

3. 开启 RAG 后无检索结果
- 先执行索引构建脚本。
- 检查 `SHELL_AGENT_RAG_DOCS` 路径是否有效。




