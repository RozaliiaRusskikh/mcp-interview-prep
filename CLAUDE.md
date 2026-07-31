# Project instructions

## Reference docs
Follow official docs as the source of truth over habit or assumption:
- **MDN** — HTML/CSS/JS/accessibility (e.g. label vs. placeholder, ARIA usage)
- **React docs** (react.dev) — component patterns, hooks
- **Python docs** — language/stdlib behavior
- **Pydantic docs** — schema/validation patterns for the backend
- **FastAPI docs** — routing, dependency injection, request/response models
- **FastMCP docs** — `mcp.server.fastmcp.FastMCP` patterns (tools/resources/prompts) in `backend/mcp/server.py`

## Golden rule
Only do what's necessary. No speculative abstractions, no unused options, no
extra files "just in case." Write code simple. Keep changes and this file
itself short.

## Backend API casing
Backend Pydantic models use `alias_generator = to_camel`. This means:
- The API always returns and expects **camelCase** field names (`lastSyncAt`, `documentCount`)
- Frontend TypeScript models must use **camelCase** to match the JSON directly

## Backend logging
Use **loguru** for backend logs — never `print`. Configure it once in
`main.py` (remove the default handler, add one sink with a fixed format —
see below); every other module just does `from loguru import logger`, no
per-module setup. The format must be **universal**: the same format string
everywhere, not varied per module or call site:
```
{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}
```
Log request routing decisions, Gemini calls, and rate-cap hits — these are
the events worth being able to see.
