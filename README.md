# mcp-interview-prep

An AI clone of Roza Russkikh that answers interview-style questions — resume facts, skills, contact info, and STAR-format behavioral situations — built as hands-on MCP practice and a portfolio piece.

## How it works

A Python MCP server (`server.py`) exposes Roza's data — `personal.json`, `resume.json`, `situations.json` — as MCP resources, tools, and prompts. Eventually a FastAPI backend acts as the MCP client: it tries deterministic keyword matching first (e.g. "conflict" → `get_situation("conflict")`, formatted directly from JSON, no LLM), and only falls back to Gemini for open-ended questions it can't confidently match. A Next.js + Tailwind chat UI talks to FastAPI over HTTP — it never talks to MCP directly.

## Stack

- **MCP server**: Python, `mcp[cli]`
- **Backend** (Phase 2): Python, FastAPI — the MCP client, also calls Gemini as a fallback
- **LLM**: Gemini via `google-generativeai`
- **Frontend** (Phase 2): Next.js + Tailwind
- **Hosting** (Phase 2): Fly.io (backend), Vercel (frontend)

## Status

**Phase 1** (current): build the MCP server and test it directly with Claude Code — no custom client needed, Claude Code is already an MCP host.

**Phase 2** (later): build the FastAPI backend as MCP client + Gemini fallback, then the Next.js frontend, then deploy.

See [PLAN.md](PLAN.md) for full design details.

## MCP server

**Resources**
- `personal://info` — values, mission, background, tone
- `situations://all` — STAR-format behavioral stories
- `resume://full` — experience, education, skills

**Tools**
- `get_situation(category: str)` — behavioral story by category (conflict, leadership, failure, ambiguity)
- `get_experience(company_or_title: str)` — one job entry
- `get_skill(skill: str)` — skill category + supporting experience highlights
- `get_contact()` — email, LinkedIn, GitHub

**Prompts**
- `find_gaps()` — reports which standard interview competencies have no situation yet
- `answer_as_roza(question: str)` — answers in Roza's voice/tone

## Run locally

```bash
uv run mcp dev server.py   # MCP Inspector
```
