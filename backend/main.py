import json
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.genai.errors import APIError
from loguru import logger
from mcp import types

import formatter
import llm
import rate_limit
import router
from mcp_client.client import MCPClient
from schemas import ChatRequest, ChatResponse

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
    allow_methods=["POST"],
    allow_headers=["*"],
)


def _parse_tool_result(result: types.CallToolResult) -> list | dict | str:
    """Reconstruct the Python value a deterministic MCP tool returned.

    Tools whose return type is a union with `str` (get_situation, get_experience,
    get_skill, get_recommendations) always populate structuredContent as
    {"result": <value>}. Tools with a plain `dict` return type (get_contact,
    get_screening_info) never populate structuredContent, so those fall back to
    parsing the single text content block as JSON.
    """
    if result.structuredContent is not None:
        return result.structuredContent["result"]
    return json.loads(result.content[0].text)


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    match = router.route(payload.question)
    if match is not None:
        result = await mcp_client.call_tool(match.tool_name, match.tool_input)
        value = _parse_tool_result(result)
        answer = formatter.format_tool_result(match.tool_name, value)
        return ChatResponse(answer=answer, source="deterministic")

    if not rate_limit.try_consume():
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    try:
        answer = await llm.answer_with_llm(payload.question, payload.history, mcp_client)
    except APIError as e:
        # Covers Gemini's own quota/availability errors (e.g. the free tier's
        # real daily cap, which can be hit before our own rate_limit counter
        # trips — that counter resets on every server restart, Gemini's doesn't).
        logger.warning(f"Gemini API error, falling back to capped message: {e}")
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    if answer is None:
        return ChatResponse(answer=rate_limit.RATE_CAPPED_MESSAGE, source="rate_capped")

    return ChatResponse(answer=answer, source="llm")
