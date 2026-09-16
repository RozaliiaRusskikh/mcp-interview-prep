import json
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.genai.errors import APIError
from langfuse import get_client, observe
from loguru import logger
from mcp import types

import formatter
import llm
import rate_limit
import router
from mcp_client.client import MCPClient
from schemas import ChatRequest, ChatResponse, Recommendation

# get_client() works even without LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY set —
# it logs a warning and the client stays disabled rather than raising. But
# @observe() on a disabled client doesn't push a real span context, so the
# explicit update_current_span/set_current_trace_io/score_current_trace calls
# below have nothing to attach to and log their own "no active span" warning
# per call if invoked anyway. LANGFUSE_ENABLED gates those explicit calls —
# @observe() itself stays harmlessly in place either way.
langfuse_client = get_client()
LANGFUSE_ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY"))

# Best-effort, live-traffic version of the same idea eval/run_eval.py checks
# per adversarial case with a tailored decline_signals list — this one has no
# foreknowledge of which case (if any) a real question resembles, so it's a
# single generic list, unioned from the dataset's adversarial cases. Measures
# whether the ANSWER declined/redirected — not a claim that the INPUT was
# classified as an attack, which would need a separate classifier this
# project doesn't have.
GENERIC_DECLINE_SIGNALS = (
    "can't share that", "can't reveal", "not able to share", "can't do that",
    "not able to", "happy to talk about", "my background", "professional background",
)

logger.remove()
logger.add(
    os.getenv("LOG_FILE", sys.stderr),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

mcp_client = MCPClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_client.connect()
    yield
    await mcp_client.cleanup()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    # Vite's dev port drifts (5173 -> 5174, ...) whenever 5173 is already taken,
    # which would otherwise CORS-fail regardless of FRONTEND_ORIGIN. Harmless in
    # prod: this regex only ever matches http://localhost, never a real domain.
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _trace_metadata(**kwargs) -> None:
    if LANGFUSE_ENABLED:
        langfuse_client.update_current_span(metadata=kwargs)


def _trace_io(input: str, output: str) -> None:
    if LANGFUSE_ENABLED:
        langfuse_client.set_current_trace_io(input=input, output=output)


def _parse_tool_result(result: types.CallToolResult) -> list | dict | str:
    """Reconstruct the Python value a deterministic MCP tool returned.

    Tools whose return type is a union with `str` (get_situation, get_experience,
    get_skill, get_recommendations) always populate structuredContent as
    {"result": <value>}. Tools with a plain, non-union return type (get_contact,
    get_screening_info, get_screening_field, get_personal_info,
    get_years_of_experience, get_education) never populate structuredContent, so
    those fall back to parsing the single text content block as JSON.
    """
    if result.structuredContent is not None:
        return result.structuredContent["result"]
    return json.loads(result.content[0].text)


@app.get("/recommendations", response_model=list[Recommendation])
async def get_recommendations() -> list[Recommendation]:
    result = await mcp_client.call_tool("get_recommendations", {})
    return _parse_tool_result(result)


@app.post("/chat", response_model=ChatResponse)
@observe(name="chat", capture_input=False, capture_output=False)
async def chat(payload: ChatRequest) -> ChatResponse:
    match = router.route(payload.question)
    if match is not None:
        result = await mcp_client.call_tool(match.tool_name, match.tool_input)
        value = _parse_tool_result(result)
        answer = formatter.format_tool_result(match.tool_name, value)
        _trace_metadata(route="deterministic", tool_name=match.tool_name, tool_input=match.tool_input)
        _trace_io(input=payload.question, output=answer)
        return ChatResponse(answer=answer, source="deterministic")

    if not rate_limit.try_consume():
        _trace_metadata(route="rate_capped")
        _trace_io(input=payload.question, output=rate_limit.RATE_CAPPED_MESSAGE)
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    try:
        llm_answer = await llm.answer_with_llm(payload.question, payload.history, mcp_client)
    except APIError as e:
        # Covers Gemini's own quota/availability errors (e.g. the free tier's
        # real daily cap, which can be hit before our own rate_limit counter
        # trips — that counter resets on every server restart, Gemini's doesn't).
        logger.warning(f"Gemini API error, falling back to capped message: {e}")
        _trace_metadata(route="llm_error", error=str(e))
        _trace_io(input=payload.question, output=rate_limit.RATE_CAPPED_MESSAGE)
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    _trace_metadata(route="llm", tool_calls=llm_answer.tool_calls)

    if llm_answer.text is None:
        _trace_io(input=payload.question, output=rate_limit.RATE_CAPPED_MESSAGE)
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    declined = any(signal in llm_answer.text.lower() for signal in GENERIC_DECLINE_SIGNALS)
    if LANGFUSE_ENABLED:
        langfuse_client.score_current_trace(name="declined_or_redirected", value=declined, data_type="BOOLEAN")
    _trace_io(input=payload.question, output=llm_answer.text)

    return ChatResponse(answer=llm_answer.text, source="llm")
