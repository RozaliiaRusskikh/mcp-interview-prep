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

## Phase 2 — detailed steps

### Backend (`backend/` folder, FastAPI)
1. `uv add fastapi uvicorn google-generativeai mcp` (or a separate `pyproject.toml` under `backend/` if kept as its own package).
2. **MCP client connection** — use the `mcp` SDK's stdio client to launch `server.py` as a subprocess and open a session (same pattern as Claude Code does, just in your own code instead of Claude Code's host).
3. **Keyword router** — a small function mapping question text to a tool call:
   - category keywords (conflict, leadership, failure, ambiguity) → `get_situation(category)`
   - company/title names from `resume.json` → `get_experience(...)`
   - known skill names → `get_skill(...)`
   - "contact" / "email" / "linkedin" / "github" → `get_contact()`
   - no confident match → fall through to LLM path
4. **Deterministic formatter** — turns each tool's JSON result into a short, readable paragraph (template strings per tool, not LLM-generated).
5. **LLM fallback** — only reached when no keyword matches: call the MCP `answer_as_roza` prompt to build the final prompt text, fetch `personal://info` for tone, then call Gemini via `google-generativeai`.
6. **`/chat` endpoint** — `POST {question: str} → {answer: str}`. Wires steps 3–5 together: router → formatter or LLM fallback → JSON response.
7. **CORS** — allow the Next.js frontend's origin (localhost during dev, the Vercel domain in prod).
8. Test locally with `curl` or the FastAPI `/docs` Swagger UI before touching the frontend.

### Frontend (`frontend/` folder, Next.js + Tailwind)
9. `npx create-next-app@latest frontend --tailwind` (App Router, TypeScript).
10. One page (`app/page.tsx`): message list state + text input + send button.
11. On send: `fetch(BACKEND_URL + "/chat", { method: "POST", body: JSON.stringify({ question }) })`, append the response to the message list.
12. `BACKEND_URL` as an environment variable (`.env.local` locally, Vercel env var in prod) — never hardcoded.
13. Basic styling only (Tailwind) — chat bubbles, scroll-to-bottom, loading state while waiting for a response.
14. Test locally against the FastAPI backend running on `localhost:8000`.

### Deployment
15. **Backend → Fly.io**: add a `Dockerfile` (or use `fly launch` which generates one for a Python app), set the `GOOGLE_API_KEY` as a Fly secret (`fly secrets set`), deploy with `fly deploy`.
16. **Frontend → Vercel**: `vercel` CLI or GitHub integration, set `BACKEND_URL` as a Vercel environment variable pointing at the deployed Fly.io URL.
17. **End-to-end verification**: open the Vercel URL, ask a keyword-matchable question (should be instant, deterministic) and an open-ended question (should hit Gemini), confirm both return sensible answers.

No database, no auth, no rate limiting in this first pass — those are reasonable additions later if the bot gets real traffic, not needed for a portfolio demo.

## Phase 3 — eval harness (LLM regression testing)

Mirrors real eval-engineering work (offline eval pipelines, precision/recall scoring, regression detection before deployment) — also doubles as practice for evaluation-focused ML roles. Tool: **Langfuse** (not LangChain — LangChain is an orchestration framework, not an eval tool; Langfuse has datasets, LLM-as-judge scoring, and run-over-run comparison built in, which is what regression detection actually needs).

1. **Instrument `/chat`** — wrap each request in a Langfuse trace (question in, router decision, tool call result, final answer out). `langfuse` Python SDK, just decorators/context managers around the existing Phase 2 code — no architecture change.
2. **Build an eval dataset in Langfuse** — a set of test questions with expected outputs:
   - Router cases: question → expected tool + expected category/argument (tests the deterministic path's precision/recall — did it pick the right tool, did it miss/misfire).
   - LLM fallback cases: open-ended question → a short rubric of facts that must appear (e.g. "mentions El Paso Labs", "mentions FastAPI") — tests the Gemini path for hallucination/drift.
3. **Tiered scoring — LLM-as-judge only where cheap checks can't do the job:**
   - Router cases: plain string/field assertions (expected tool name == actual tool name). No LLM call at all — it's deterministic, a judge would be pure waste.
   - LLM fallback cases, tier 1: keyword/fact-presence check (does the answer contain the required facts as substrings) — cheap, deterministic, catches most regressions (missing facts, wrong company name, etc.).
   - LLM fallback cases, tier 2 (only if tier 1 is ambiguous or the rubric item can't be substring-matched — e.g. tone, "does this contradict a fact" paraphrased differently): escalate that single case to an LLM-as-judge call. Most cases should never reach this tier.
4. **Pass threshold = 0.8** — a dataset run passes if ≥80% of cases score correct (router precision/recall combined with fallback pass-rate). Below 0.8 = regression, flagged before deploying.
5. **Run the eval suite offline** — triggered manually (or in CI before a deploy), against the fixed dataset, not on live production traffic. `langfuse` dataset run, scoring every test case via the tiered logic above, producing one aggregate score checked against the 0.8 threshold. Live/online eval on real user questions is a possible future addition, not part of this pass.
6. **Regression detection** — re-run the same dataset after any change (new situations, prompt tweak, model swap) and diff scores against the previous run; a drop below 0.8, or any drop relative to the prior run even if still above 0.8, gets flagged — the same way the resume's "offline eval pipeline... detect LLM regressions before production deployment" describes.
7. **Explainability** — for each failed case, Langfuse shows the trace (input → router decision → tool result → LLM call → output) so a failure can be diagnosed, not just flagged — mirrors "explain a score to a candidate who believes they were assessed unfairly" from the job description.

Depends on Phase 2 existing (router + Gemini fallback) — nothing to regression-test before that.
