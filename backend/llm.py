import os

from google import genai
from google.genai import types

from mcp_client.client import MCPClient

MODEL_NAME = "gemini-2.5-flash"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily create the Gemini client from the server-side GOOGLE_API_KEY env var."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


async def answer_with_llm(question: str, mcp: MCPClient) -> str:
    """Answer an open-ended question via Gemini, grounded in Roza's data.

    Renders the `answer_as_roza` MCP prompt as-is for the model turn — it already
    constrains the model's role/limits and segregates the untrusted `question` from
    the trusted grounding data (personal.json values/background/tone) baked into the
    prompt text, per CLAUDE.md's "Prompt injection defense". The live MCP session is
    passed as a tool so Gemini can call get_situation, get_experience, get_skill,
    get_contact, get_recommendations, and get_screening_info itself while answering.
    """
    messages = await mcp.get_prompt("answer_as_roza", {"question": question})
    contents = [
        types.Content(
            role=message.role,
            parts=[types.Part.from_text(text=message.content.text)],
        )
        for message in messages
    ]

    response = await _get_client().aio.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(tools=[mcp.session()]),
    )
    return response.text
