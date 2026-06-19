# Plan: AI Clone / Interview-Prep Bot (full scope)

## Context
Building a portfolio piece: an AI clone of Roza that answers interview-style questions (including behavioral/STAR situations), doubling as hands-on MCP practice. Stack already agreed:
- **MCP server** (Python, `mcp[cli]`) — exposes personal data as resources/tools/prompts
- **Backend** (Python, FastAPI) — MCP client; on each request calls MCP tool(s), then calls Gemini with that context + the question
- **LLM**: Gemini via `google-generativeai` SDK
- **Frontend**: Next.js + Tailwind chat UI, POSTs to FastAPI `/chat`
- **Hosting**: Fly.io (backend), Vercel (frontend)

Split into two phases:
- **Phase 1 (this pass)**: build the MCP server, test it directly with Claude Code — Claude Code is already an MCP host/client, so no custom client code needed yet.
- **Phase 2 (later)**: build the FastAPI backend as a custom MCP client connecting to this same `server.py`. It calls the MCP tools/resources, then passes that context to Gemini. The Next.js frontend only talks to FastAPI over HTTP — it never talks to MCP directly.
  - Request flow in `/chat`: try deterministic keyword matching first (map the question to a tool call — e.g. "conflict" → `get_situation("conflict")` — and format the returned JSON into readable text directly, no LLM involved). Only fall back to Gemini + the `answer_as_roza` prompt when no keyword match is confident enough. This keeps most answers fast, free, and 100% accurate (no hallucination risk on factual data), and reserves the LLM for open-ended/ambiguous questions where rigid matching would fail.

## MCP server design

**Data files** (JSON, in repo root):
- `personal.json` — new (values, mission, background, tone)
- `situations.json` — new. Array of STAR entries: `id`, `category` (conflict, leadership, failure, ambiguity), `situation`, `task`, `action`, `result`.
- `resume.json` — new. Structured resume: `experience` (list of `{title, company, dates, highlights}`), `education`, `skills`. This is the actual work-history data, distinct from `personal.json` (values/tone) and `situations.json` (behavioral stories).

**`server.py`** (`mcp.server.fastmcp.FastMCP`), one shared `_load_json(path)` helper reused everywhere:

- **Resources** (bulk reads):
  - `personal://info` → `personal.json`
  - `situations://all` → `situations.json`
  - `resume://full` → `resume.json`
- **Tools** (targeted lookups):
  - `get_situation(category: str)` → case-insensitive substring filter on category; falls back to listing available categories if no match
  - `get_experience(company_or_title: str)` → single experience entry by company/title match
  - `get_skill(skill: str)` → case-insensitive match against `resume.json` skills categories; returns the matching category (ai_and_backend / frontend / tools) plus any experience highlights mentioning that skill, so "do you know X" answers come with a concrete example
  - `get_contact()` → returns email, LinkedIn, and GitHub from `resume.json.contact`
- **Prompts** (reusable workflows):
  - `find_gaps()` → tells Claude to read `situations://all`, diff against standard competency list (leadership, conflict, failure/learning, ambiguity, influence without authority, scale/tradeoffs), report gaps
  - `answer_as_roza(question: str)` → template instructing the model to answer in Roza's voice/tone (from `personal://info`) using whichever resource/tool result is relevant

This MCP server is consumed two ways, both already in scope:
1. Directly by Claude Code (project-scoped `.mcp.json`) — useful for your own interview practice sessions.
2. By the FastAPI backend acting as MCP client, which calls these same tools/resources before calling Gemini — this is what powers the public-facing chat bot.
