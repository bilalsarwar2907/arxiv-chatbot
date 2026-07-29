# arxiv-chatbot — MCP Rich-Context AI App

A multi-server MCP (Model Context Protocol) chatbot that searches arXiv, fetches web content, and manages a local filesystem — built as part of the DeepLearning.AI course *"MCP: Build Rich-Context AI Apps with Anthropic."*

## Overview

This project demonstrates three ways to run an MCP setup:

1. **Custom Client** — a Python chatbot (`mcp_chatbot.py`) that connects to multiple MCP servers simultaneously and routes tool calls to the right one.
2. **Claude Desktop as Client** — the same servers wired directly into Claude Desktop via config, no custom client needed.
3. **Remote SSE Server** — the research server exposed over HTTP/SSE so any MCP client (e.g. MCP Inspector) can connect remotely.

## Architecture

```
MODE 1 — Custom Client:
OpenRouter (claude-haiku-4-5)
        ↓
  mcp_chatbot.py  (MCP Client)
        ├── filesystem   (npx @modelcontextprotocol/server-filesystem) [stdio]
        ├── research     (uv run research_server.py) [stdio]
        └── fetch        (venv Python → python -m mcp_server_fetch) [stdio]

MODE 2 — Claude Desktop as Client:
Claude Desktop
        ├── filesystem   [stdio]
        ├── research     [stdio]
        └── fetch        [stdio]

MODE 3 — Remote SSE Server:
MCP Inspector / any SSE client
        └── research_server.py running at http://127.0.0.1:8001/sse [SSE]
```

## Features

- **Tools** — `search_papers()` and `extract_info()` query the arXiv API directly.
- **Resources** — `papers://folders` and `papers://{topic}` expose saved research as read-only, GET-style endpoints.
- **Prompts** — `generate_search_prompt(topic, num_papers)` is a reusable, parameterized prompt template.
- **Multi-server routing** — `AsyncExitStack` and a `tool_to_session` map let one client talk to filesystem, research, and fetch servers at once.
- **Chat commands**:
  ```
  /prompts                          list available prompts
  /prompt generate_search_prompt topic=transformers num_papers=5
  @folders                          list saved topics
  @machine_learning                 papers in that topic
  search transformers               LLM searches and summarises
  ```

## Setup

```powershell
cd C:\Users\biges\arxiv-chatbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `mcp_project/` with:
```
OPENROUTER_API_KEY=your_key_here
```

### Dependencies (pinned)
- `mcp==1.28.1` — do **not** upgrade to 2.0.0, it breaks the filesystem and fetch servers.
- `mcp-server-fetch==2025.1.17`

## Running

**Custom client (Mode 1):**
```powershell
cd mcp_project
uv run mcp_chatbot.py
```

**Claude Desktop (Mode 2):**
Add the `mcpServers` block below to `%APPDATA%\Claude\claude_desktop_config.json` (absolute paths required), then relaunch Claude Desktop.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\biges\\arxiv-chatbot\\mcp_project"]
    },
    "research": {
      "command": "uv",
      "args": ["run", "C:\\Users\\biges\\arxiv-chatbot\\mcp_project\\research_server.py"]
    },
    "fetch": {
      "command": "C:\\Users\\biges\\arxiv-chatbot\\venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server_fetch"]
    }
  }
}
```

**Remote SSE server (Mode 3):**
```powershell
# Terminal 1 — keep running
cd mcp_project
uv run research_server.py
# Server runs at http://127.0.0.1:8001

# Terminal 2 — inspector
npx @modelcontextprotocol/inspector
# Connect to: http://127.0.0.1:8001/sse
```

If port 8001 is already in use:
```powershell
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

## Concepts Reference

| Concept | Purpose | Decorator | Example |
|---------|---------|-----------|---------|
| Tools | Perform actions, have side effects | `@mcp.tool()` | `search_papers()` |
| Resources | Read-only data, like GET endpoints | `@mcp.resource()` | `papers://folders` |
| Prompts | Reusable prompt templates | `@mcp.prompt()` | `generate_search_prompt()` |

| Transport | Use case | Client import | URL suffix |
|-----------|----------|---------------|------------|
| stdio | Local servers, launched as subprocess | `stdio_client` | N/A |
| SSE | Remote servers (legacy) | `sse_client` | `/sse` |
| Streamable HTTP | Remote servers (modern) | `streamablehttp_client` | `/mcp/` |

## Known Issues & Fixes

| Bug | Cause | Fix |
|-----|-------|-----|
| `fetch: Connection closed` | uvx used mcp 2.0.0, venv had 1.28.1 | Point server_config at venv Python directly |
| `Method not found` on filesystem/fetch | `list_resources()` / `list_prompts()` not supported by those servers | Wrap calls in `try/except pass` |
| `AttributeError: no attribute 'cleanup'` | Duplicate `async def main():` | Remove duplicate |
| `asyncio.run()` inside `main()` | Indentation error | Move to module level |
| OpenRouter 404 loop | Anthropic SDK incompatible with OpenRouter | Switch to OpenAI SDK |
| mcp 2.0.0 broke all servers | Protocol breaking change | Pin `mcp==1.28.1` |
| Port 8001 WinError 10048 | Old process still holding the port | `netstat -ano | findstr :8001` then `taskkill /PID` |

## Status

Course complete — all lessons (3–9) implemented and verified across all three modes.

## Credits

Built while completing *"MCP: Build Rich-Context AI Apps with Anthropic"* (DeepLearning.AI).
