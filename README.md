# mcp-interview-prep

An AI clone of Roza Russkikh that answers interview-style questions — resume facts, skills, contact info, and STAR-format behavioral situations — built as hands-on MCP practice and a portfolio piece.

## How it works

A Python MCP server (`backend/mcp_server/server.py`) exposes Roza's data — `backend/mcp_server/data/personal.json`, `backend/mcp_server/data/resume.json`, `backend/mcp_server/data/situations.json` — as MCP resources, tools, and prompts. It lives inside `backend/` (not a sibling folder) so Render's backend deployment — scoped to the `backend/` directory only — can actually reach it; Render has no access to files outside a service's configured root directory. Eventually a FastAPI backend acts as the MCP client: it tries deterministic keyword matching first (e.g. "conflict" → `get_situation("conflict")`, formatted directly from JSON, no LLM), and only falls back to Gemini (rate-capped, Roza's own key — no user key required) for open-ended questions it can't confidently match. Pydantic models validate the `/chat` request/response shape and the data loaded from the MCP tools. A React + Tailwind chat UI talks to FastAPI over HTTP — it never talks to MCP directly.

## Stack

- **MCP server**: Python, `mcp[cli]`
- **Backend** (Phase 2): Python, FastAPI — the MCP client (spawns the MCP server as a subprocess), also calls Gemini as a rate-capped fallback; Pydantic models for all request/response/tool-output schemas
- **LLM**: Gemini via `google-genai`, Roza's own free-tier key, server-side only
- **Frontend** (Phase 2): React (Vite, TypeScript) + Tailwind
- **Hosting** (Phase 2): Render (backend, free tier), Vercel (frontend)
- **Eval** (Phase 3): offline eval pipeline (Langfuse) — see PLAN.md

## Status

**Phase 1** (current): MCP server built, unit-tested, and verified via the MCP Inspector. Final step: live-test all resources/tools/prompts through Claude Code itself (`.mcp.json` is already configured to auto-connect).

**Phase 2** (later): build the FastAPI backend as MCP client + Gemini fallback, then the React frontend, then deploy.

**Phase 3** (later): offline eval pipeline for regression testing the router + Gemini fallback.

See [PLAN.md](PLAN.md) for full design details.

## MCP server

**Resources**
- `personal://info` — values, mission, background, tone
- `situations://all` — STAR-format behavioral stories
- `resume://full` — experience, education, skills
- `recommendations://all` — LinkedIn recommendations from managers, colleagues, mentors, teachers

**Tools**
- `get_situation(category: str)` — behavioral story by category (conflict, challenge, deadline, disagreement, initiative, ownership, problem-solving)
- `get_experience(company_or_title: str)` — one job entry
- `get_skill(skill: str)` — skill category + supporting experience highlights
- `get_contact()` — email, LinkedIn, GitHub
- `get_recommendations(name: str = "")` — one person's recommendation, or all of them if no name given
- `get_screening_info()` — work authorization/visa status and EEO self-identification
- `get_years_of_experience(domain: str = "total")` — years of experience (total, or qa/react/angular/frontend/backend), computed live from real dates, never hardcoded

**Prompts**
- `find_gaps()` — reports which standard interview competencies have no situation yet
- `answer_as_roza()` — persona/tone/boundary instructions for answering as Roza; meant to be used as the model's system instruction, with the visitor's question passed separately as user content

## Run locally

```bash
uv run mcp dev mcp_server/server.py   # MCP Inspector
uv run pytest mcp_server/tests/       # unit tests
```
