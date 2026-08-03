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
