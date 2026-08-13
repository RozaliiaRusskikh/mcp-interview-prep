import os

from google import genai
from loguru import logger

from mcp_client.client import MCPClient
from schemas import ChatMessage

MODEL_NAME = "gemini-2.5-flash"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily create the Gemini client from the server-side GOOGLE_API_KEY env var."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


async def answer_with_llm(question: str, history: list[ChatMessage], mcp: MCPClient) -> str:
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
        # Must be a plain dict, not a GenerateContentConfig object: the SDK
        # deep-copies object configs before extracting MCP sessions, and a live
        # ClientSession can't be deepcopy'd (unpicklable asyncio internals).
        # Dict configs skip that deep copy. https://github.com/googleapis/python-genai/issues/2669
        config={"system_instruction": system_instruction, "tools": [mcp.session()]},
    )
    return response.text
