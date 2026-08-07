import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

DATA_DIR = Path(__file__).parent / "mcp_server" / "data"

CONTACT_KEYWORDS = ("contact", "email", "phone", "linkedin", "github", "reach")


def _load_json(filename: str):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _contains_word(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase.lower())}\b", text) is not None


@dataclass
class RouteMatch:
    tool_name: str
    tool_input: dict


def route(question: str) -> Optional[RouteMatch]:
    """Match a question to an MCP tool by keyword, or return None to fall through to the LLM."""
    match = _match(question.lower())
    if match is not None:
        logger.info(f"Routed question to {match.tool_name}({match.tool_input})")
    else:
        logger.info("No keyword match for question — falling through to LLM")
    return match


def _match(q: str) -> Optional[RouteMatch]:
    situations = _load_json("situations.json")
    for category in sorted({s["category"] for s in situations}):
        if _contains_word(q, category):
            return RouteMatch("get_situation", {"category": category})

    resume = _load_json("resume.json")
    companies_and_titles = {e["company"] for e in resume["experience"]} | {
        e["title"] for e in resume["experience"]
    }
    for token in sorted(companies_and_titles):
        if _contains_word(q, token):
            return RouteMatch("get_experience", {"company_or_title": token})

    skills = sorted(skill for group in resume["skills"].values() for skill in group)
    for skill in skills:
        if _contains_word(q, skill):
            return RouteMatch("get_skill", {"skill": skill})

    recommendations = _load_json("recommendations.json")
    for name in sorted({r["name"] for r in recommendations}):
        if _contains_word(q, name):
            return RouteMatch("get_recommendations", {"name": name})

    if any(_contains_word(q, kw) for kw in CONTACT_KEYWORDS):
        return RouteMatch("get_contact", {})

    return None
