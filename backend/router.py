import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

DATA_DIR = Path(__file__).parent / "mcp_server" / "data"

CONTACT_KEYWORDS = ("contact", "email", "phone", "linkedin", "github", "reach")

YEARS_OF_EXPERIENCE_PHRASES = (
    "years of experience",
    "how many years",
    "how long have you been",
    "how long have you worked",
)

# Catches phrasings/typos that miss the exact phrases above but still clearly
# ask about duration, e.g. "How many of Angular experience do you have?"
# (dropped "years") or "How much backend experience do you have?".
YEARS_OF_EXPERIENCE_LEAD_INS = ("how many", "how much", "how long")

YEARS_OF_EXPERIENCE_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "qa": ("qa", "quality assurance", "testing"),
    "react": ("react",),
    "angular": ("angular",),
    "frontend": ("frontend", "front-end", "front end"),
    "backend": ("backend", "back-end", "back end"),
}

# Situation categories are framed as positive stories (e.g. "deadline" holds a
# story about *meeting* a tight deadline). A negated question ("missed a
# deadline", "failed at ownership") asks for the opposite of what that story
# shows, so a keyword match would return a misleading answer — skip the
# category match on negation and let it fall through to the LLM instead,
# which won't misrepresent the story (see the answer_as_roza prompt's
# "do not invent experience" instruction).
NEGATION_WORDS = ("missed", "failed", "fail", "didn't", "never", "haven't", "couldn't", "wouldn't")


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
    is_negated = any(_contains_word(q, w) for w in NEGATION_WORDS)

    situations = _load_json("situations.json")
    if not is_negated:
        for category in sorted({s["category"] for s in situations}):
            if _contains_word(q, category):
                return RouteMatch("get_situation", {"category": category})

    resume = _load_json("resume.json")

    is_years_question = any(phrase in q for phrase in YEARS_OF_EXPERIENCE_PHRASES) or (
        "experience" in q and any(lead in q for lead in YEARS_OF_EXPERIENCE_LEAD_INS)
    )
    if is_years_question:
        domain = None
        for candidate, keywords in YEARS_OF_EXPERIENCE_DOMAIN_KEYWORDS.items():
            if any(kw in q for kw in keywords):
                domain = candidate
                break

        if domain is None:
            # No tracked domain matched. If the question names a specific
            # skill we just don't track years for (e.g. "years of AWS"),
            # defaulting to "total" would confidently answer the wrong
            # question — fall through to the LLM instead, same reasoning as
            # the negation handling above.
            all_skills = (s for group in resume["skills"].values() for s in group)
            if not any(_contains_word(q, skill) for skill in all_skills):
                domain = "total"

        if domain is not None:
            return RouteMatch("get_years_of_experience", {"domain": domain})
        return None

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
        # Match on first or last name alone too — visitors rarely type a
        # recommender's full name ("What does Ivan say?", "Ivan V's take?").
        if any(_contains_word(q, part) for part in name.split()):
            return RouteMatch("get_recommendations", {"name": name})

    if any(_contains_word(q, kw) for kw in CONTACT_KEYWORDS):
        return RouteMatch("get_contact", {})

    return None
