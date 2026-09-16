# backend

FastAPI backend for the interview-prep chat UI. Acts as the MCP client for
`mcp_server/server.py` (launched as a stdio subprocess), tries deterministic
keyword matching against the MCP tools first, and falls back to Gemini
(rate-capped) for open-ended questions. See [../PLAN.md](../PLAN.md) for the
full design.

## Run locally

```bash
uv sync
uv run uvicorn main:app --reload
```

## Eval suite

Deterministic regression tests against `eval/dataset.json` — no LLM-as-judge,
no backend server required (imports `router.py`/`llm.py` directly). Most cases
call the real Gemini API, so this needs `GOOGLE_API_KEY` set and takes a
couple of minutes; Langfuse dataset-run upload is optional (skipped silently
without `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`).

Run from the **repo root** (not from inside `backend/`) — `--project backend`
is relative to the current directory:

```bash
uv run --project backend backend/eval/run_eval.py
```

Prints PASS/FAIL per case and an aggregate score, and exits `0` if it's
**≥ 0.9**, `1` otherwise — gateable by a CI/deploy step (see `TASKS.md` T042).

**When to run it:**
- After changing `mcp_server/server.py`'s persona/tool instructions or any
  tool's docstring — these directly steer what Gemini decides to call
- After adding/editing resume, situations, personal, or recommendations data
- After swapping the Gemini model or changing `temperature`/`thinking_config`
- Before deploying, generally — re-run and diff against the last known score
  rather than trusting a single prior run, since real-model non-determinism
  and Gemini's own transient errors mean the score varies run to run; a
  single run below 0.9 isn't automatically a regression, but a *consistent*
  drop across a few runs is worth investigating
