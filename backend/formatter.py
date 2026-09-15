from typing import Any, Callable


def format_situation(situations: list[dict]) -> str:
    return " ".join(
        f"{s['situation']} {s['task']} {s['action']} {s['result']}"
        for s in situations
    )


def format_experience(experiences: list[dict]) -> str:
    return " ".join(
        f"{e['title']} at {e['company']} ({e['dates']})"
        + (f" — {e['company_description']}" if e.get("company_description") else "")
        + f": {'; '.join(e['highlights'])}"
        for e in experiences
    )


def format_skill(skill: dict) -> str:
    if skill["supporting_highlights"]:
        return ". ".join(skill["supporting_highlights"])
    return f"Yes, I have experience with {skill['skill']}."


def format_contact(contact: dict) -> str:
    return (
        f"Email: {contact['email']} · Phone: {contact['phone']} · "
        f"LinkedIn: {contact['linkedin']} · GitHub: {contact['github']} · "
        f"Location: {contact['location']}"
    )


def format_personal_info(data: dict) -> str:
    return data["text"]


def format_screening_info(screening: dict) -> str:
    return (
        f"Target role: {screening['target_role']} "
        f"{screening['work_authorization']} "
        f"Salary expectation: {screening['salary_expectation']} "
        f"Relocation: {screening['relocation']}"
    )


def format_recommendations(recommendations: list[dict]) -> str:
    return " ".join(
        f"{r['name']} ({r['title']}) — {r['relationship']}, {r['date']}: "
        f"\"{r['quote']}\""
        for r in recommendations
    )


YEARS_OF_EXPERIENCE_LABELS = {
    "total": "professional software engineering experience",
    "qa": "QA experience",
    "react": "React experience",
    "angular": "Angular experience",
    "frontend": "frontend experience",
    "backend": "backend experience",
    "full_stack": "full-stack experience",
}


def _format_period(period: dict) -> str:
    return (
        f"since {period['start']}"
        if period["end"] == "Present"
        else f"from {period['start']} to {period['end']}"
    )


def format_years_of_experience(data: dict) -> str:
    label = YEARS_OF_EXPERIENCE_LABELS[data["domain"]]
    year_word = "year" if data["years"] == 1 else "years"
    # Multiple separate stints (e.g. a gap doing something else in between) get
    # each spelled out and joined, rather than implying one continuous stretch.
    span = " and ".join(_format_period(p) for p in data["periods"])
    return f"I have about {data['years']} {year_word} of {label}, {span}."


FORMATTERS: dict[str, Callable[[Any], str]] = {
    "get_situation": format_situation,
    "get_experience": format_experience,
    "get_skill": format_skill,
    "get_contact": format_contact,
    "get_screening_info": format_screening_info,
    "get_screening_field": format_personal_info,
    "get_personal_info": format_personal_info,
    "get_recommendations": format_recommendations,
    "get_years_of_experience": format_years_of_experience,
}


def format_tool_result(tool_name: str, result: list[dict] | dict | str) -> str:
    """Turn a raw MCP tool result into readable text.

    Tools already return a human-readable string for the not-found case
    (e.g. "No situations found for category 'x'...") — pass those through
    as-is rather than templating them.
    """
    if isinstance(result, str):
        return result
    return FORMATTERS[tool_name](result)
