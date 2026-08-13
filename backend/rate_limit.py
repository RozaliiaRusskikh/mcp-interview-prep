from datetime import datetime, timezone

from loguru import logger

# Gemini's actual free-tier daily limit for gemini-2.5-flash is 20 requests/day
# (not the ~1500/day higher tiers get) — keep this under that with headroom for
# non-chat testing, since it's what's supposed to prevent hitting Gemini's own
# 429 in the first place.
DAILY_CAP = 15

RATE_CAPPED_MESSAGE = (
    "I'm not sure how to match that one — try asking about my experience, "
    "skills, a specific project, or a behavioral situation like "
    "conflict/ownership/deadlines."
)

_call_counts: dict[str, int] = {}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def try_consume() -> bool:
    """Record a Gemini call against today's cap, if there's room.

    Returns False (without recording) once DAILY_CAP is hit for the day —
    the caller should skip the Gemini call and use RATE_CAPPED_MESSAGE instead.
    """
    today = _today()
    if _call_counts.get(today, 0) >= DAILY_CAP:
        logger.warning(f"Daily Gemini rate cap ({DAILY_CAP}) hit for {today}")
        return False
    _call_counts[today] = _call_counts.get(today, 0) + 1
    return True
