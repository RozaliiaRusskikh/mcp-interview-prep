# Tasks: Monorepo restructure + Phase 2 (backend + frontend)

**Input**: [PLAN.md](PLAN.md)
**Prerequisites**: Phase 1 MCP server complete (`server.py`, `data/*.json`, `tests/` — done, currently at repo root)

Conventions:
- `[ ]` pending, `[x]` done
- `[P]` = safe to do in parallel with other `[P]` tasks in the same phase (touches different files, no shared dependency)
- Every task names the exact file(s) it touches

**Order note**: Frontend (Phase A below) is being scaffolded first, ahead of the `mcp/` restructure and backend — it has no dependency on either (it talks to `VITE_BACKEND_URL` over HTTP, not to the MCP server directly), and scaffolding it now lets UI work proceed using the `frontend-design` skill while backend/mcp work is pending.

---

## Phase A: Frontend (`frontend/`) — React + Vite + Tailwind

- [x] T016 `npm create vite@latest frontend -- --template react-ts`; add Tailwind (v4, via `@tailwindcss/vite` + `@theme` tokens in `src/index.css`; design concept/rationale in `frontend/DESIGN.md`)
- [x] T017 `frontend/src/Chat.tsx` — message list state, text input, send button
- [x] T018 `frontend/src/Chat.tsx` — POST to `${VITE_BACKEND_URL}/chat`, append response to message list, loading state
- [x] T019 [P] `frontend/.env.local` — `VITE_BACKEND_URL=http://localhost:8000`
- [x] T020 Verify: frontend dev server renders and handles input locally — confirmed via `npm run build` (clean) and Playwright-CLI screenshots of the empty state and the question/error-card state (backend not up yet, so the fetch fails gracefully as expected)

## Phase 0: Monorepo restructure

- [ ] T001 Create `mcp/` folder; `git mv server.py mcp/server.py`, `git mv data mcp/data`, `git mv tests mcp/tests`
- [ ] T002 Update `.mcp.json` command path to point at `mcp/server.py`
- [ ] T003 Update `DATA_DIR` in `mcp/server.py` if the relative path assumption changes (it shouldn't — `Path(__file__).parent` still resolves correctly after the move, but verify)
- [ ] T004 Verify: `uv run mcp dev mcp/server.py` (Inspector) and `uv run pytest mcp/tests/` both pass
- [ ] T005 Update `README.md` run instructions and `PLAN.md` file references to the new `mcp/` paths

## Phase 1: Backend (`backend/`) — FastAPI MCP client + Gemini fallback

- [ ] T006 Scaffold `backend/` with its own `pyproject.toml`; add deps: `fastapi`, `uvicorn`, `google-generativeai`, `mcp`, `pydantic`
- [ ] T007 `backend/mcp_client.py` — stdio client that launches `mcp/server.py` as a subprocess and opens an MCP session
- [ ] T008 [P] `backend/schemas.py` — `ChatRequest`, `ChatResponse` (`answer`, `source: Literal["deterministic","llm","rate_capped"]`)
- [ ] T009 [P] `backend/schemas.py` — per-tool output models: `Situation`, `Experience`, `Skill`, `Contact`
- [ ] T010 `backend/router.py` — keyword router: category/company/skill/contact keywords → matching MCP tool call, else fall through
- [ ] T011 `backend/formatter.py` — deterministic tool-JSON → readable-text templates, one per tool
- [ ] T012 `backend/llm.py` — Gemini fallback via `answer_as_roza` MCP prompt + `personal://info`, using server-side `GOOGLE_API_KEY`
- [ ] T013 `backend/rate_limit.py` — in-memory daily counter capping Gemini calls; graceful deterministic message when capped
- [ ] T014 `backend/main.py` — `POST /chat` wiring T010–T013 together, validated against T008/T009 schemas; CORS for the frontend origin
- [ ] T015 Verify: run backend locally, exercise `/chat` via `curl`/Swagger (`/docs`) for both a deterministic and an LLM-fallback question

## Phase 3: Local end-to-end verification

- [ ] T021 Ask a keyword-matchable question through the UI — confirm deterministic path, no Gemini call
- [ ] T022 Ask an open-ended question — confirm Gemini fallback answers correctly, grounded in real data
- [ ] T023 Manually trip the rate cap — confirm graceful fallback message

## Phase 4: Deployment (Render backend + Vercel frontend)

**Prerequisites**: Phase 1 (backend) and Phase 3 (local e2e verification) complete — don't deploy an unverified backend.

### Backend → Render

- [ ] T024 `backend/render.yaml` — Render Blueprint: native Python runtime (no `Dockerfile` needed — no system deps beyond Python), build command (`pip install -r requirements.txt` or `uv sync`), start command (`uvicorn backend.main:app --host 0.0.0.0 --port $PORT`)
- [ ] T025 [P] In the Render dashboard: create the web service from the GitHub repo, root directory `backend/`, free tier
- [ ] T026 [P] Set `GOOGLE_API_KEY` as a Render environment secret (dashboard only — never committed)
- [ ] T027 Enable auto-deploy on push to `main`
- [ ] T028 Verify: deployed Render URL responds on `/chat` (curl or `/docs` Swagger UI) for both a deterministic and an LLM question; confirm cold-start behavior after ~15 min idle (expect 30-60s on first request)

### Frontend → Vercel

- [ ] T029 [P] Connect the GitHub repo to Vercel (dashboard or `vercel` CLI), set root directory to `frontend/`
- [ ] T030 Set `VITE_BACKEND_URL` as a Vercel environment variable, pointing at the Render URL from T028
- [ ] T031 Verify: Vercel deploy succeeds; production URL renders the app (Chat + Recommendations pages) with no console errors

### End-to-end (production)

- [ ] T032 On the live Vercel URL, ask a keyword-matchable question — confirm instant deterministic answer, no Gemini call
- [ ] T033 Ask an open-ended question — confirm Gemini fallback answers correctly, grounded in real data
- [ ] T034 Temporarily lower the daily rate cap, trip it, confirm the graceful fallback message appears in the UI, then revert the cap
- [ ] T035 Update `README.md` with the live frontend/backend URLs and the Render cold-start caveat

---

Not included here (tracked separately in [PLAN.md](PLAN.md)): the Phase 3 eval harness (Langfuse) — add as a follow-up `TASKS.md` phase once the app is deployed end-to-end.
