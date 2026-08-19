# arxiv-chatbot — Roadmap

---

## PROJECT STATE

| Field | Value |
|---|---|
| Current Phase | Post-Course |
| Current Objective | Establish project baseline — awaiting next direction from user |
| Current Verified Step | Session 1 complete — full codebase review done |
| Next Verified Step | Awaiting user instruction |
| Last Updated | 2026-08-19 |
| Active Risks | `requirements.txt` lacks version pins; `.env` location mismatch; Anthropic SDK → OpenRouter non-standard usage in `mcp_chatbot.py` |
| Last Session | Session 1 — arxiv-chatbot Baseline Review |

---

## DECISION REGISTRY

| ID | Date | Decision | Reason | Status | Session |
|---|---|---|---|---|---|
| D-001 | 2026-08-19 | Adopt project-continuity working mode | Structured session handover and single source of truth | Active | Session 1 |
| D-002 | 2026-08-19 | Do NOT upgrade `mcp` beyond 1.28.1 | Version 2.0.0 introduces breaking changes that break the filesystem and fetch servers | Active | Session 1 |

---

## PROJECT OVERVIEW

**Repository:** https://github.com/bilalsarwar2907/arxiv-chatbot  
**Local path:** `C:\Users\biges\arxiv-chatbot`  
**Origin:** DeepLearning.AI course — *"MCP: Build Rich-Context AI Apps with Anthropic"* (Lessons 3–9)  
**Language:** Python 3, Windows, venv

### File Structure

```
C:\Users\biges\arxiv-chatbot\
├── chatbot.py              — Simple single-turn chatbot (OpenAI SDK → OpenRouter)
├── tools.py                — arXiv tool definitions + execute_tool dispatcher
├── main.py                 — Test runner (calls execute_tool directly)
├── requirements.txt        — Python dependencies (WARNING: unpinned)
├── .env                    — API key (root level)
├── papers/                 — Local paper cache
│   ├── machine_learning/papers_info.json
│   └── transformers/papers_info.json
└── mcp_project/
    ├── mcp_chatbot.py      — Full MCP client (Anthropic SDK → OpenRouter, multi-server)
    ├── research_server.py  — FastMCP server (tools + resources + prompts, SSE)
    ├── server_config.json  — MCP server connection config
    └── papers/             — Separate paper cache for mcp_project scope
        ├── machine_learning/papers_info.json
        └── transformers/papers_info.json
```

### Three Operating Modes

| Mode | Entry Point | Transport | Notes |
|---|---|---|---|
| 1 — Custom Client | `uv run mcp_chatbot.py` (from `mcp_project/`) | stdio → 3 servers | Full MCP multi-server routing |
| 2 — Claude Desktop | Claude Desktop + `claude_desktop_config.json` | stdio | No custom client needed |
| 3 — Remote SSE | `uv run research_server.py` + MCP Inspector | SSE at `:8001` | Research server only |

### Key Capabilities

- **Tools:** `search_papers(topic, max_results)` — queries arXiv, saves JSON locally; `extract_info(paper_id)` — retrieves saved paper metadata
- **Resources:** `papers://folders` — lists saved topics; `papers://{topic}` — lists papers in a topic
- **Prompts:** `generate_search_prompt(topic, num_papers)` — reusable parameterised prompt template
- **Chat commands:** `/prompts`, `/prompt <name> [key=value …]`, `@folders`, `@<topic>`, `quit`
- **Multi-server routing:** `AsyncExitStack` + `tool_to_session` dict maps each tool name to the session that owns it

### Dependencies (Critical)

| Package | Version in venv | Pin status | Note |
|---|---|---|---|
| mcp | 1.28.1 | **Must stay pinned** | 2.0.0 breaks filesystem + fetch |
| mcp-server-fetch | 2025.1.17 | Pinned | — |
| anthropic | 0.120.0 | Unpinned in requirements.txt | Used in mcp_chatbot.py |
| openai | latest | Unpinned | Used in chatbot.py for OpenRouter |
| arxiv | 4.0.0 | Unpinned | arXiv API client |
| python-dotenv | latest | Unpinned | — |
| nest_asyncio | latest | Unpinned | — |

---

## KNOWN ISSUES

| ID | Issue | Location | Severity | Status |
|---|---|---|---|---|
| K-001 | `requirements.txt` has no version pins — a fresh install could pull `mcp==2.0.0` and break all servers | `requirements.txt` | **Medium** | Open |
| K-002 | `.env` file is at project root; README instructs placing it inside `mcp_project/` — discrepancy may confuse new contributors | `.env` vs README | Low | Open |
| K-003 | `mcp_chatbot.py` uses Anthropic SDK with a custom `base_url` pointing at OpenRouter (non-standard) — fragile if OpenRouter changes their API shape | `mcp_chatbot.py` L24-27 | Low | Open |
| K-004 | `execute_prompt()` picks the first session arbitrarily instead of routing to the session that owns the named prompt | `mcp_chatbot.py` L127-129 | Low | Open |

---

## SESSION HISTORY

---

### Session 1 — arxiv-chatbot Baseline Review

**Session Number:** 1  
**Date/Time:** 2026-08-19  
**Objectives:** Establish project state, review full codebase, create authoritative roadmap

**Key Concepts Discussed:**
- MCP (Model Context Protocol) architecture with stdio and SSE transports
- Multi-server routing via `AsyncExitStack` and `tool_to_session` map in `mcp_chatbot.py`
- FastMCP server exposing tools, resources, and prompts via `research_server.py`
- OpenRouter as LLM provider (Anthropic SDK path in `mcp_chatbot.py`; OpenAI SDK path in `chatbot.py`)
- Version pinning risk: `mcp==1.28.1` must not be upgraded

**Decisions Made:**
- D-001: Adopt project-continuity working mode
- D-002: Do NOT upgrade `mcp` beyond 1.28.1

**Technical Findings:**
- Project is a completed DeepLearning.AI course exercise — all lessons (3–9) implemented and verified across all three modes
- There are two separate `papers/` directories: one at root (used by `chatbot.py`/`tools.py`) and one inside `mcp_project/` (used by `research_server.py`) — both contain populated JSON caches
- `requirements.txt` lists packages without version pins (K-001)
- `mcp_chatbot.py` uses `Anthropic(api_key=..., base_url="https://openrouter.ai/api")` — non-standard OpenRouter usage (K-003)
- `server_config.json` correctly points the research and fetch servers at the venv Python executable — this is the documented workaround for the mcp 2.0.0 / uvx conflict
- `main.py` is a simple test runner, not a production entry point

**Files Reviewed:**
- `README.md`, `chatbot.py`, `tools.py`, `main.py`, `requirements.txt`
- `mcp_project/mcp_chatbot.py`, `mcp_project/research_server.py`, `mcp_project/server_config.json`

**Files Created:** `arxiv-chatbot - Roadmap.md` (this file)  
**Files Modified:** None  
**Files Deleted:** None  
**Code Snippets Created or Updated:** None  
**Implementations Completed:** None  
**Problems Encountered:** None  
**Resolutions Applied:** None  
**Research Performed:** GitHub repo fetch + local filesystem scan + full source file review  
**Important References:** https://github.com/bilalsarwar2907/arxiv-chatbot  
**Risks and Limitations:** K-001 through K-004 (see Known Issues above)  
**Assumptions Made:** Project is on Windows; venv is at `C:\Users\biges\arxiv-chatbot\venv`  
**Outstanding Issues:** K-001 through K-004  
**Pending Tasks:** Awaiting user direction on next phase  
**Open Questions:** What does Bilal want to do next — bug fixes, new features, deployment, refactoring?

---

#### Starting Point for Next Session

**Current project status:** Course complete. All three modes implemented and verified. No active development underway. Roadmap created.

**What was completed this session:** Full codebase review — all source files read, architecture understood, known issues catalogued (K-001 to K-004), authoritative roadmap created and saved to project.

**What remains to be done:** Determined by user. Possible directions:
- Fix K-001 (pin versions in `requirements.txt`)
- Fix K-002 (consolidate `.env` location)
- Fix K-003 (switch `mcp_chatbot.py` to OpenAI SDK for consistency)
- Fix K-004 (route prompt execution to the correct session)
- Extend features (web UI, more MCP servers, streaming, conversation history)
- Deploy SSE server remotely
- Port to `mcp==2.0.0` when ready

**Verified next step:** None — awaiting user instruction.

**Relevant file names and locations:**
- `C:\Users\biges\arxiv-chatbot\mcp_project\mcp_chatbot.py` — main MCP client
- `C:\Users\biges\arxiv-chatbot\mcp_project\research_server.py` — MCP research server
- `C:\Users\biges\arxiv-chatbot\requirements.txt` — dependency list (unpinned — K-001)
- `C:\Users\biges\arxiv-chatbot\.env` — OpenRouter API key

**Required context to resume work:** Read Project State + this Starting Point block. No additional context needed.

**Known issues:** K-001 (unpinned requirements), K-002 (.env location), K-003 (Anthropic SDK → OpenRouter non-standard), K-004 (prompt session routing)

**Dependencies:** OpenRouter API key, Node.js (for filesystem MCP server via npx), uv (for running scripts)

**Required human actions:** User must decide next development direction.

**Critical decisions that must not be lost:**
- D-002: Do NOT upgrade `mcp` beyond `1.28.1` — version 2.0.0 breaks the filesystem and fetch servers.
