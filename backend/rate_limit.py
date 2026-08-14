from datetime import datetime, timezone

from loguru import logger

# Sized to bound worst-case spend on gemini-2.5-flash-lite (thinking off) to
# under $5/month, not to Gemini's free-tier request limit — this project pays.
# At ~2,000 input + ~300 output tokens per exchange ($0.10 / $0.40 per 1M
# tokens), one call costs ~$0.00032; 500/day * 30 days ≈ $4.80/month if the
# cap is hit every single day. Real usage well below the cap costs far less.
# Pair this with a monthly spend cap in AI Studio as a backstop.
DAILY_CAP = 500

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
