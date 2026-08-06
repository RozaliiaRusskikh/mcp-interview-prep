from typing import Any, Callable


def format_situation(situations: list[dict]) -> str:
    return " ".join(
        f"{s['situation']} {s['task']} {s['action']} {s['result']}"
        for s in situations
    )


def format_experience(experiences: list[dict]) -> str:
    return " ".join(
        f"{e['title']} at {e['company']} ({e['dates']}): {'; '.join(e['highlights'])}"
        for e in experiences
    )


def format_skill(skill: dict) -> str:
    category = skill["category"].replace("_", " ")
    text = f"{skill['skill']} falls under {category}."
    if skill["supporting_highlights"]:
        text += " " + " ".join(skill["supporting_highlights"])
    return text


def format_contact(contact: dict) -> str:
    return (
        f"Email: {contact['email']} · Phone: {contact['phone']} · "
        f"LinkedIn: {contact['linkedin']} · GitHub: {contact['github']} · "
        f"Location: {contact['location']}"
    )


def format_recommendations(recommendations: list[dict]) -> str:
    return " ".join(
        f"{r['name']} ({r['title']}) — {r['relationship']}, {r['date']}: "
        f"\"{r['quote']}\""
        for r in recommendations
    )


FORMATTERS: dict[str, Callable[[Any], str]] = {
    "get_situation": format_situation,
    "get_experience": format_experience,
    "get_skill": format_skill,
    "get_contact": format_contact,
    "get_recommendations": format_recommendations,
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
