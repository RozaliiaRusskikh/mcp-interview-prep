# mcp-interview-prep

An AI clone of Roza Russkikh that answers interview-style questions — resume facts, skills, contact info, education, screening info, and STAR-format behavioral situations — built as hands-on MCP practice and a portfolio piece.

## How it works

A Python MCP server (`backend/mcp_server/server.py`) exposes Roza's data — `backend/mcp_server/data/{personal,resume,situations,recommendations}.json` — as MCP resources, tools, and prompts. It lives inside `backend/` (not a sibling folder) so Render's backend deployment — scoped to the `backend/` directory only — can actually reach it; Render has no access to files outside a service's configured root directory.

A FastAPI backend (`backend/main.py`) acts as the MCP client: for every question, it tries deterministic keyword matching first (`backend/router.py` — e.g. "conflict" → `get_situation("conflict")`, formatted directly from JSON, no LLM), and only falls back to Gemini (rate-capped, Roza's own key — no user key required) for open-ended questions it can't confidently match. On the Gemini path, the live MCP session is handed to the model as a tool, so Gemini can call the same tools itself mid-answer — grounded in real data, never its own training, by design (though nothing *forces* it to call one; see "A real caveat" below). Pydantic models validate the `/chat` request/response shape and every tool's output schema.

**MCP resources exist but aren't part of the answer pipeline**: they're readable by any MCP client (Claude Code, MCP Inspector) but the `google-genai` SDK's tool-calling integration only discovers `@mcp.tool()`-decorated functions, not `@mcp.resource()` ones — confirmed by reading the SDK source directly. Every fact Gemini can ground an answer in comes from a tool call, not a resource read.

A React + Tailwind UI talks to FastAPI over HTTP — it never talks to MCP directly. This includes `GET /recommendations` (backing the Recommendations page): FastAPI calls the same `get_recommendations` MCP tool Gemini uses and returns it as JSON, so `recommendations.json` stays the single source of truth instead of also being hardcoded into the frontend.

### A real caveat, by design

Nothing forces Gemini to call a tool before answering (`AUTO` mode — the alternative, forcing every call, breaks multi-turn tool-calling outright; tested and reverted). This has caused real, observed failures — a fabricated relocation city, a sycophantic non-denial of skills Roza doesn't have — each fixed and locked in as a regression case in `eval/dataset.json`. `backend/llm.py` logs a warning any time Gemini answers without calling a tool, so an ungrounded answer is visible in logs instead of indistinguishable from a real one.

## Stack

- **MCP server**: Python, `mcp[cli]` (`backend/mcp_server/`)
- **Backend**: Python, FastAPI — the MCP client (spawns the MCP server as a subprocess), also calls Gemini as a rate-capped fallback; Pydantic models for all request/response/tool-output schemas
- **LLM**: Gemini (`gemini-2.5-flash-lite`) via `google-genai`, Roza's own key, server-side only
- **Frontend**: React (Vite, TypeScript) + Tailwind
- **Tracing**: Langfuse (`backend/main.py`'s `/chat` endpoint; optional — no-ops without credentials)
- **Eval**: deterministic offline eval harness, no LLM-as-judge (`eval/run_eval.py` + `eval/dataset.json`) — see [PLAN.md](PLAN.md)
- **Hosting**: Render (backend), Vercel (frontend)

## Status

**MCP server**: built, unit-tested, verified via MCP Inspector and Claude Code itself (`.mcp.json` auto-connects).

**Backend + frontend**: built and working locally — deterministic router, Gemini fallback with tool-calling, chat UI.

**Eval harness**: `eval/dataset.json` (router, LLM-fallback, and adversarial/jailbreak cases — all with real regression cases from bugs found during development) and `eval/run_eval.py` (deterministic scoring, 0.9 pass threshold, exits non-zero on regression) are built and passing.

See [PLAN.md](PLAN.md) and [TASKS.md](TASKS.md) for full design and task-level status.

## MCP server

**Resources** (readable by MCP clients directly; not used by Gemini's tool-calling — see "How it works" above)
- `personal://info` — values, mission, background, tone
- `situations://all` — STAR-format behavioral stories
- `resume://full` — experience, education, skills, contact
- `recommendations://all` — LinkedIn recommendations from managers, colleagues, mentors, teachers

**Tools**
- `get_situation(category)` — behavioral story by category (a fixed `Literal` set: ambiguity, challenge, conflict, deadline, disagreement, failure, initiative, ownership, prioritization, problem-solving, scale/tradeoffs, technical judgment, what I would do differently)
- `get_experience(company_or_title: str)` — one job entry (splits highlights by named party for combined employer|client fields, e.g. an outsourcing engagement)
- `get_skill(skill: str)` — skill category + supporting experience highlights
- `get_education()` — school, credential, and year for each degree/certificate
- `get_contact()` — email, phone, preferred name, LinkedIn, GitHub, location
- `get_recommendations(name: str = "")` — one person's recommendation, or all of them if no name given
- `get_years_of_experience(domain)` — years of experience (total, or qa/react/angular/frontend/backend), computed live from real dates, never hardcoded
- `get_screening_info()` — the full screening picture: target role, work authorization, salary expectation, relocation preference, strongest languages (ranked), EEO self-identification. Prefer this for multi-topic questions.
- `get_screening_field(field)` — exactly one screening topic (target role, work authorization, salary, or relocation) — used instead of `get_screening_info` when a question asks about only one, so the answer doesn't bundle in unrelated info
- `get_personal_info(field)` — exactly one identity fact: name, motto, mission, values, background story, strengths beyond the resume, countries lived in, or future vision (most of this is also baked directly into Gemini's system prompt; this tool makes the same facts reachable deterministically too)

## HTTP API

- `POST /chat` — `{ question, history }` in, `{ answer, source }` out (`source` is `deterministic`, `llm`, or `rate_capped`)
- `GET /recommendations` — all LinkedIn recommendations, read via the `get_recommendations` MCP tool (not a direct file read) so the frontend never needs its own copy of `recommendations.json`

**Prompts**
- `find_gaps()` — reports which standard interview competencies have no situation yet
- `answer_as_roza()` — persona/tone/boundary instructions for answering as Roza; meant to be used as the model's system instruction, with the visitor's question passed separately as user content (prompt-injection defense: trusted instructions and untrusted input travel as structurally distinct channels, never concatenated into one message)

## Run locally

```bash
# MCP server — Inspector + unit tests
uv run mcp dev backend/mcp_server/server.py
uv run pytest backend/mcp_server/tests/

# Backend (needs backend/.env — see backend/.env.example)
cd backend && uv run uvicorn main:app --reload

# Frontend (needs frontend/.env.local — see frontend/.env.example)
cd frontend && npm install && npm run dev

# Eval suite (from repo root — see backend/README.md for full details)
uv run --project backend eval/run_eval.py
```
