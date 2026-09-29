import os
from dataclasses import dataclass, field

from google import genai
from loguru import logger

from mcp_client.client import MCPClient
from schemas import ChatMessage

MODEL_NAME = "gemini-2.5-flash-lite"

# maximum_remote_calls (SDK default: 10) caps sequential turns, but a single
# turn can itself contain many parallel function_call parts — observed once
# (2026-08-17), not reproducible on retry: one question triggered 3,290
# get_experience calls in what the SDK still counted as a single turn. A
# turn requesting more tools than any real question here would ever need is
# itself the signal something degenerate happened, regardless of whether the
# resulting text looks fine — treat it as unsafe rather than trust it.
MAX_SANE_TOOL_CALLS = 20

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily create the Gemini client from the server-side GOOGLE_API_KEY env var."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


@dataclass
class LLMAnswer:
    text: str | None
    # Names of tools Gemini actually invoked while producing this answer
    # (empty if it answered from pattern-completion without looking anything
    # up). Exposed so callers — the eval harness's expected_tool_calls check,
    # in particular — can verify grounding directly, not just infer it from
    # whether the final text happens to contain the right words.
    tool_calls: list[str] = field(default_factory=list)


async def answer_with_llm(question: str, history: list[ChatMessage], mcp: MCPClient) -> LLMAnswer:
    """Answer an open-ended question via Gemini, grounded in Roza's data.

    Renders the `answer_as_roza` MCP prompt (persona/tone/boundaries, no question
    baked in) as a real Gemini system_instruction, and sends prior turns plus the
    visitor's `question` as separate user/model content. This is a stronger
    untrusted/trusted split than a "Question:" text label inside one combined
    message — the model sees system instructions and conversational content as
    structurally distinct channels, per CLAUDE.md's "Prompt injection defense"
    (segregate untrusted content). The live MCP session is passed as a tool so
    Gemini can call get_situation, get_experience, get_skill, get_contact,
    get_education, get_recommendations, get_screening_info, get_screening_field,
    get_personal_info, and get_years_of_experience itself while answering.
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
    tool_calls = _tool_calls_made(response)
    if len(tool_calls) > MAX_SANE_TOOL_CALLS:
        logger.error(
            f"Gemini ({MODEL_NAME}) made {len(tool_calls)} tool calls answering {question!r} "
            f"— treating as a degenerate response, discarding text regardless of content"
        )
        return LLMAnswer(text=None, tool_calls=tool_calls)
    if response.text is None:
        # Gemini 2.5 models can end a turn right after a function call with no
        # trailing text part — .text has nothing to join, so it's None rather
        # than "". Log finish_reason so a recurrence is diagnosable.
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        logger.warning(f"Gemini ({MODEL_NAME}) returned no text (finish_reason={finish_reason})")
    elif not tool_calls:
        # Nothing forces Gemini to call a tool before answering — it can
        # pattern-complete a plausible-sounding answer from training data
        # instead (the 2026-08-16 "Austin, TX" hallucination). This doesn't
        # block the answer, just makes an ungrounded one visible in the logs
        # instead of silently indistinguishable from a real one.
        logger.warning(f"Gemini ({MODEL_NAME}) answered {question!r} without calling any tool — possibly ungrounded")
    return LLMAnswer(text=response.text, tool_calls=tool_calls)


def _tool_calls_made(response) -> list[str]:
    """Names of every tool Gemini actually invoked while producing this response."""
    history = response.automatic_function_calling_history or []
    return [
        part.function_call.name
        for content in history
        for part in (content.parts or [])
        if part.function_call is not None and part.function_call.name is not None
    ]
