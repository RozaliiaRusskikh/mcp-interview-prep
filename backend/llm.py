import os

from google import genai
from loguru import logger

from mcp_client.client import MCPClient
from schemas import ChatMessage

MODEL_NAME = "gemini-2.5-flash-lite"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily create the Gemini client from the server-side GOOGLE_API_KEY env var."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


async def answer_with_llm(question: str, history: list[ChatMessage], mcp: MCPClient) -> str | None:
    """Answer an open-ended question via Gemini, grounded in Roza's data.

    Renders the `answer_as_roza` MCP prompt (persona/tone/boundaries, no question
    baked in) as a real Gemini system_instruction, and sends prior turns plus the
    visitor's `question` as separate user/model content. This is a stronger
    untrusted/trusted split than a "Question:" text label inside one combined
    message — the model sees system instructions and conversational content as
    structurally distinct channels, per CLAUDE.md's "Prompt injection defense"
    (segregate untrusted content). The live MCP session is passed as a tool so
    Gemini can call get_situation, get_experience, get_skill, get_contact,
    get_recommendations, get_screening_info, and get_years_of_experience itself
    while answering.
    """
    system_messages = await mcp.get_prompt("answer_as_roza", {})
    system_instruction = system_messages[0].content.text

    contents = [
        {"role": "user" if msg.role == "user" else "model", "parts": [{"text": msg.content}]}
        for msg in history
    ]
    contents.append({"role": "user", "parts": [{"text": question}]})

    logger.info(f"Calling Gemini ({MODEL_NAME}) for question: {question!r} ({len(history)} prior turns)")
    response = await _get_client().aio.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config={
            "system_instruction": system_instruction,
            "tools": [mcp.session()],
            "thinking_config": {"thinking_budget": 512},
            # Near-0, not exactly 0: Gemini clamps temperature=0 to a small
            # epsilon internally anyway, and flash-lite's tool-orchestration
            # gets noticeably less reliable at true 0 in practice. Lower
            # temperature -> more consistent argument extraction/tool choice
            # across repeated identical questions — directly targets the
            # run-to-run inconsistency observed in the C# sycophancy case
            # (same question, two different answers on different runs).
            "temperature": 0.1,
        },
    )
    if response.text is None:
        # Gemini 2.5 models can end a turn right after a function call with no
        # trailing text part — .text has nothing to join, so it's None rather
        # than "". Log finish_reason so a recurrence is diagnosable.
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        logger.warning(f"Gemini ({MODEL_NAME}) returned no text (finish_reason={finish_reason})")
    elif not _called_a_tool(response):
        # Nothing forces Gemini to call a tool before answering — it can
        # pattern-complete a plausible-sounding answer from training data
        # instead (the 2026-08-16 "Austin, TX" hallucination). This doesn't
        # block the answer, just makes an ungrounded one visible in the logs
        # instead of silently indistinguishable from a real one.
        logger.warning(f"Gemini ({MODEL_NAME}) answered {question!r} without calling any tool — possibly ungrounded")
    return response.text


def _called_a_tool(response) -> bool:
    history = response.automatic_function_calling_history or []
    return any(
        part.function_call is not None
        for content in history
        for part in (content.parts or [])
    )
