import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

DATA_DIR = Path(__file__).parent / "mcp_server" / "data"

CONTACT_KEYWORDS = ("contact", "email", "phone", "linkedin", "github", "reach")

SCREENING_FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "work_authorization": (
        "visa", "sponsorship", "work authorization", "authorized to work",
        "citizen", "green card", "permanent resident",
    ),
    "salary_expectation": ("salary", "compensation", "pay rate", "pay range"),
    "relocation": ("relocate", "relocating", "relocation"),
    "target_role": ("target role", "targeting", "what role are you", "what position are you"),
}

PERSONAL_INFO_FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "name": ("last name", "full name", "first name", "your name"),
    "motto": ("motto",),
    "mission": ("your mission", "career mission"),
    "values": ("your values", "what do you value"),
    "background_story": ("your journey", "your story", "career path", "non-linear path", "how did you get into"),
    "strengths_beyond_resume": ("your strengths", "what are your strengths"),
    "lived_in": ("lived in", "where have you lived", "countries have you lived"),
    "future_vision": ("where do you see yourself", "future plans", "long term goals", "long-term goals", "career goals"),
}

YEARS_OF_EXPERIENCE_PHRASES = (
    "years of experience",
    "how many years",
    "how long have you been",
    "how long have you worked",
)

YEARS_OF_EXPERIENCE_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "qa": ("qa", "quality assurance", "testing"),
    "react": ("react",),
    "angular": ("angular",),
    "frontend": ("frontend", "front-end", "front end"),
    "backend": ("backend", "back-end", "back end"),
    "full_stack": ("full stack", "full-stack", "fullstack"),
}

UNTRACKED_YEARS_QUALIFIERS = (
    "startup", "start-up",
    "language", "languages",
    "skill", "skills",
)

ELABORATION_PHRASES = ("day-to-day", "day to day")

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

    is_years_question = any(phrase in q for phrase in YEARS_OF_EXPERIENCE_PHRASES)
    if is_years_question:
        domain = None
        for candidate, keywords in YEARS_OF_EXPERIENCE_DOMAIN_KEYWORDS.items():
            if any(kw in q for kw in keywords):
                domain = candidate
                break

        if domain is None:
            # No tracked domain matched. If the question names a specific
            # skill we just don't track years for (e.g. "years of AWS"), or
            # an untracked qualifier like "startup", defaulting to "total"
            # would confidently answer the wrong question — fall through to
            # the LLM instead, same reasoning as the negation handling above.
            all_skills = (s for group in resume["skills"].values() for s in group)
            mentions_untracked_qualifier = any(_contains_word(q, kw) for kw in UNTRACKED_YEARS_QUALIFIERS)
            if not mentions_untracked_qualifier and not any(_contains_word(q, skill) for skill in all_skills):
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

    if not any(phrase in q for phrase in ELABORATION_PHRASES):
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

    for field, keywords in SCREENING_FIELD_KEYWORDS.items():
        if any(_contains_word(q, kw) for kw in keywords):
            return RouteMatch("get_screening_field", {"field": field})

    for field, keywords in PERSONAL_INFO_FIELD_KEYWORDS.items():
        if any(_contains_word(q, kw) for kw in keywords):
            return RouteMatch("get_personal_info", {"field": field})

    if any(_contains_word(q, kw) for kw in CONTACT_KEYWORDS):
        return RouteMatch("get_contact", {})

    return None
