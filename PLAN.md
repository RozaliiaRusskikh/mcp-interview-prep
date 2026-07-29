# Plan: AI Clone / Interview-Prep Bot (full scope)

## Context
Building a portfolio piece: an AI clone of Roza that answers interview-style questions (including behavioral/STAR situations), doubling as hands-on MCP + React practice. Stack already agreed:
- **MCP server** (Python, `mcp[cli]`) — exposes personal data as resources/tools/prompts
- **Backend** (Python, FastAPI) — MCP client; on each request calls MCP tool(s), then calls Gemini with that context + the question. Pydantic models validate both the `/chat` request/response shape and the data coming back from MCP tool calls (see Backend step 3) — a deliberate practice goal alongside FastAPI.
- **LLM**: Gemini via `google-generativeai` SDK — Roza's own free-tier key, server-side only. No bring-your-own-key flow: recruiters are the audience, and requiring them to get an API key before they can chat is friction that defeats the point of the demo.
- **Frontend**: React (Vite, TypeScript) + Tailwind chat UI, POSTs to FastAPI `/chat`. Plain React (not Next.js) — the point of this project includes hands-on React practice (routing/state/fetch without framework magic).
- **Hosting**: Render (backend, free web service tier), Vercel (frontend). Not Fly.io — its free tier now requires a card on file and isn't a good fit for a zero-cost portfolio demo; Render's free tier needs no card (tradeoff: it sleeps after ~15 min idle and cold-starts on the next request, which is fine for a demo people click into occasionally).
- **Eval**: offline eval pipeline (Langfuse) run against a versioned dataset, gated before deploy — see Phase 3 below. Included in scope, not a maybe-later.

**Monolith structure**: MCP's client/server split is a real process boundary (FastAPI launches `server.py` as a stdio subprocess), so it can't fully merge away — but it stays an implementation detail *inside* the backend, not a third service. One repo, subfolders (`mcp/` or repo root for the server, `backend/`, `frontend/`), and exactly **two deployable units**: the backend (FastAPI process that spawns the MCP server itself) and the frontend (static React build). Deployed and operated like a normal two-tier app.

**What "deterministic" means here**: MCP is just a transport — it isn't deterministic or not by itself. What's deterministic is the tools on the other end (`get_situation`, `get_experience`, `get_skill`, `get_contact`): plain Python functions doing JSON lookups/string matching, same input → same output every time, no model involved. The only non-deterministic step in the whole system is the Gemini fallback (an LLM can phrase things differently call to call) — the router's job is to minimize how often that path is hit.

Split into two phases:
- **Phase 1 (this pass)**: build the MCP server, test it directly with Claude Code — Claude Code is already an MCP host/client, so no custom client code needed yet.
- **Phase 2 (later)**: build the FastAPI backend as a custom MCP client connecting to this same `server.py`. It calls the MCP tools/resources, then passes that context to Gemini. The React frontend only talks to FastAPI over HTTP — it never talks to MCP directly.
  - Request flow in `/chat`: try deterministic keyword matching first (map the question to a tool call — e.g. "conflict" → `get_situation("conflict")` — and format the returned JSON into readable text directly, no LLM involved). Only fall back to Gemini + the `answer_as_roza` prompt when no keyword match is confident enough. This keeps most answers fast, free, and 100% accurate (no hallucination risk on factual data), and reserves the LLM for open-ended/ambiguous questions where rigid matching would fail — which also keeps Gemini usage low enough that a single free-tier key, rate-capped, comfortably covers portfolio-level traffic.

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
1. `uv add fastapi uvicorn google-generativeai mcp pydantic` (or a separate `pyproject.toml` under `backend/` if kept as its own package; `pydantic` ships with FastAPI but pin it explicitly since schemas are a deliberate practice goal here).
2. **MCP client connection** — use the `mcp` SDK's stdio client to launch `server.py` as a subprocess and open a session (same pattern as Claude Code does, just in your own code instead of Claude Code's host).
3. **Pydantic schemas** (`backend/schemas.py`) — two layers:
   - **API I/O**: `ChatRequest` (`question: str`) and `ChatResponse` (`answer: str`, `source: Literal["deterministic", "llm", "rate_capped"]` — useful for the frontend to badge how an answer was produced, and for the eval pipeline to check trajectory). FastAPI uses these directly as the `/chat` endpoint's request/response models, so validation and OpenAPI docs (`/docs`) come for free.
   - **MCP tool output validation**: one model per tool result shape (`Situation`, `Experience`, `Skill`, `Contact`), parsed immediately after each MCP tool call (`Situation.model_validate(result)`) before it reaches the formatter. This catches drift between `data/*.json` and what the formatter/LLM prompt expects at the boundary, rather than failing deep in string-templating code.
4. **Keyword router** — a small function mapping question text to a tool call:
   - category keywords (conflict, leadership, failure, ambiguity) → `get_situation(category)`
   - company/title names from `resume.json` → `get_experience(...)`
   - known skill names → `get_skill(...)`
   - "contact" / "email" / "linkedin" / "github" → `get_contact()`
   - no confident match → fall through to LLM path
5. **Deterministic formatter** — turns each tool's JSON result into a short, readable paragraph (template strings per tool, not LLM-generated).
6. **LLM fallback** — only reached when no keyword matches: call the MCP `answer_as_roza` prompt to build the final prompt text, fetch `personal://info` for tone, then call Gemini via `google-generativeai`, using Roza's own `GOOGLE_API_KEY` (server-side env var/secret, never sent to the frontend).
7. **Rate cap on the Gemini path** — a simple counter (in-memory is fine for a single Render instance; e.g. a module-level dict keyed by UTC date) tracking calls made today, capped well under Gemini's free-tier daily limit (e.g. 100/day vs. Gemini's ~1500/day). When the cap is hit, skip the Gemini call and return a graceful deterministic message instead (e.g. "I'm not sure how to match that one — try asking about my experience, skills, a specific project, or a behavioral situation like conflict/ownership/deadlines"). This is the only "quota" concept in the app — there's no per-user key, so no BYOK UI, no key-entry form, nothing for a visitor to configure.
8. **`/chat` endpoint** — `POST` using the `ChatRequest`/`ChatResponse` Pydantic models from step 3. Wires steps 4–7 together: router → formatter or (capped) LLM fallback → JSON response.
9. **CORS** — allow the React frontend's origin (localhost during dev, the Vercel domain in prod).
10. Test locally with `curl` or the FastAPI `/docs` Swagger UI before touching the frontend.

### Frontend (`frontend/` folder, React + Vite + Tailwind)
11. `npm create vite@latest frontend -- --template react-ts`, then add Tailwind.
12. One main view (`src/App.tsx` or a `Chat` component): message list state + text input + send button.
13. On send: `fetch(BACKEND_URL + "/chat", { method: "POST", body: JSON.stringify({ question }) })`, append the response to the message list.
14. `BACKEND_URL` as a Vite env var (`VITE_BACKEND_URL` in `.env.local` locally, Vercel env var in prod) — never hardcoded.
15. Basic styling only (Tailwind) — chat bubbles, scroll-to-bottom, loading state while waiting for a response.
16. Test locally against the FastAPI backend running on `localhost:8000`.

### Deployment
17. **Backend → Render**: free web service tier, no card required. Add a `Dockerfile` (or use Render's native Python runtime with a start command), set `GOOGLE_API_KEY` as a Render environment secret, deploy via GitHub integration (auto-deploy on push). Note: free tier sleeps after ~15 min idle and cold-starts (~30-60s) on the next request — acceptable for a portfolio demo, not for real traffic.
18. **Frontend → Vercel**: `vercel` CLI or GitHub integration, set `VITE_BACKEND_URL` as a Vercel environment variable pointing at the deployed Render URL.
19. **End-to-end verification**: open the Vercel URL, ask a keyword-matchable question (should be instant, deterministic) and an open-ended question (should hit Gemini), confirm both return sensible answers, and confirm the rate-cap fallback message appears once the daily cap is (manually, for testing) hit.

No database, no auth in this first pass — the rate cap covers the cost-control need; auth/db are reasonable additions later if the bot gets real traffic, not needed for a portfolio demo.

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
