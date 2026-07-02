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

**Data files** (JSON, in `data/`):
- `personal.json` — values, mission, background, tone.
- `situations.json` — array of real STAR entries: `id`, `category` (conflict, challenge, deadline, disagreement, initiative, ownership, problem-solving), `situation`, `task`, `action`, `result`.
- `resume.json` — structured resume: `contact`, `experience` (list of `{title, company, dates, highlights}`), `education`, `skills`. This is the actual work-history data, distinct from `personal.json` (values/tone) and `situations.json` (behavioral stories).

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
  - `find_gaps()` → computes the diff deterministically in Python (situations' categories vs. a hardcoded standard competency list: leadership, conflict, failure, ambiguity, influence without authority, scale/tradeoffs), then hands Claude the pre-computed covered/missing lists to summarize and suggest stories for
  - `answer_as_roza(question: str)` → embeds Roza's values/background/tone directly in the prompt text (loaded from `personal.json` in Python, not a separate fetch), instructing the model to answer in first person, grounded in the get_situation/get_experience/get_skill/get_contact tools or resources

This MCP server is consumed two ways, both already in scope:
1. Directly by Claude Code (project-scoped `.mcp.json`) — useful for your own interview practice sessions.
2. By the FastAPI backend acting as MCP client, which calls these same tools/resources before calling Gemini — this is what powers the public-facing chat bot.

**Phase 1 status**: `server.py`, `.mcp.json`, and `data/*.json` are built; unit tests in `tests/test_server.py` (pytest) cover the happy/not-found path for every tool plus the resources and prompts — all passing. Verified standalone via `uv run mcp dev server.py` (MCP Inspector). Remaining: live verification through Claude Code itself.

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

Mirrors real eval-engineering work (offline eval pipelines, precision/recall scoring, regression detection before deployment) — also doubles as practice for evaluation-focused ML roles. Tool: **Langfuse** (Langfuse has datasets, LLM-as-judge scoring, and run-over-run comparison built in, which is what regression detection actually needs).

Incorporates current best practices from Anthropic (keep evals simple and programmatic), LangChain/LangSmith (curated dataset with reference outputs, CI-gated thresholds), and LangGraph (evaluate the *trajectory* — tool selection and argument accuracy — not just the final answer text):

1. **Instrument `/chat`** — wrap each request in a Langfuse trace (question in, router decision, tool call + arguments, tool result, final answer out). `langfuse` Python SDK, just decorators/context managers around the existing Phase 2 code — no architecture change.
2. **Build a versioned eval dataset** — checked into the repo (e.g. `eval/dataset.json`) and synced to Langfuse, so changes to test cases are tracked in git like any other code change:
   - Router cases: question → expected tool name **and** expected arguments (e.g. `get_situation` called with `category="conflict"`, not just "some tool was called") — trajectory-level check, not just final output.
   - LLM fallback cases: open-ended question → a short rubric of facts that must appear (e.g. "mentions El Paso Labs", "mentions FastAPI") — tests the Gemini path for hallucination/drift.
3. **Tiered scoring — LLM-as-judge only where cheap checks can't do the job** (deterministic tests stay the largest share, per best practice):
   - Router cases: plain string/field assertions on tool name + arguments. No LLM call at all — it's deterministic, a judge would be pure waste.
   - LLM fallback cases, tier 1: keyword/fact-presence check (does the answer contain the required facts as substrings) — cheap, deterministic, catches most regressions (missing facts, wrong company name, etc.).
   - LLM fallback cases, tier 2 (only if tier 1 is ambiguous or the rubric item can't be substring-matched — e.g. tone, "does this contradict a fact" paraphrased differently): escalate that single case to an LLM-as-judge call, **temperature=0**, run 3x with majority-vote for stability since this tier is rare and cheap to repeat. Most cases should never reach this tier.
4. **Pass threshold = 0.8** — a dataset run passes if ≥80% of cases score correct (trajectory accuracy + fallback pass-rate combined). Below 0.8 = regression, flagged before deploying.
5. **Run the eval suite offline, gated in CI** — triggered manually or as a CI step before deploy (`pytest`-style, alongside the existing `tests/` suite), against the fixed versioned dataset, not on live production traffic. `langfuse` dataset run, scoring every test case via the tiered logic above, producing one aggregate score checked against the 0.8 threshold — fail the pipeline if it's not met. Live/online eval on real user questions is a possible future addition, not part of this pass.
6. **Regression detection** — re-run the same dataset after any change (new situations, prompt tweak, model swap) and diff scores against the previous run; a drop below 0.8, or any drop relative to the prior run even if still above 0.8, gets flagged — the same way the resume's "offline eval pipeline... detect LLM regressions before production deployment" describes. Track latency alongside correctness (Langfuse captures this automatically from the traces).
7. **Explainability** — for each failed case, Langfuse shows the full trace (input → router decision → tool call/arguments → tool result → LLM call → output) so a failure can be diagnosed at the step that broke, not just flagged — mirrors "explain a score to a candidate who believes they were assessed unfairly" from the job description.

Depends on Phase 2 existing (router + Gemini fallback) — nothing to regression-test before that.
