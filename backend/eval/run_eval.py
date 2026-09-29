"""Deterministic eval runner for backend/main.py's /chat behavior.

No LLM-as-judge anywhere — every case in backend/eval/dataset.json is scored by plain
string/field checks, per the reasoning in PLAN.md's eval harness section:
code-based grading is the most reliable method when the case allows for it,
and every case here does. Router cases call router.route() directly (pure,
no I/O). LLM-fallback and adversarial cases call llm.answer_with_llm()
directly, the same function backend/main.py's /chat endpoint calls — this
exercises the real grounding/tool-calling path, just via import instead of
an HTTP round-trip, so the eval suite doesn't require the backend server to
be running.

Usage: uv run --project backend backend/eval/run_eval.py
Exit code 0 if the aggregate score meets PASS_THRESHOLD, 1 otherwise
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from google.genai.errors import APIError

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

import llm  # noqa: E402
import router  # noqa: E402
from mcp_client.client import MCPClient  # noqa: E402

DATASET_PATH = Path(__file__).parent / "dataset.json"
PASS_THRESHOLD = 0.9


@dataclass
class CaseResult:
    category: str
    question: str
    passed: bool
    detail: str


def score_router_case(case: dict) -> tuple[bool, str]:
    match = router.route(case["question"])
    if case.get("expect_no_route"):
        if match is not None:
            return False, f"expected no deterministic route (LLM fallthrough), got {match.tool_name}({match.tool_input})"
        return True, "ok"
    if match is None:
        return False, "expected a deterministic route, got none (fell through to LLM)"
    if match.tool_name != case["expected_tool"]:
        return False, f"expected tool {case['expected_tool']!r}, got {match.tool_name!r}"
    if match.tool_input != case["expected_args"]:
        return False, f"expected args {case['expected_args']!r}, got {match.tool_input!r}"
    return True, "ok"


def score_text(answer: str, case: dict) -> tuple[bool, str]:
    """Shared fact-presence/absence/order checks, used by both llm_fallback and adversarial cases."""
    lower = answer.lower()

    missing = [f for f in case.get("expected_facts", []) if f.lower() not in lower]
    if missing:
        return False, f"missing expected facts: {missing}"

    forbidden = [f for f in case.get("must_not_contain", []) if f.lower() in lower]
    if forbidden:
        return False, f"contains forbidden text: {forbidden}"

    order = case.get("expected_order")
    if order:
        positions = [lower.find(f.lower()) for f in order]
        if any(p == -1 for p in positions):
            return False, f"expected_order fact(s) missing entirely: {order}"
        if positions != sorted(positions):
            return False, f"facts present but out of order, expected: {order}"

    decline_signals = case.get("decline_signals")
    if decline_signals and not any(sig.lower() in lower for sig in decline_signals):
        return False, "none of the expected decline/redirect signals found"

    return True, "ok"


async def score_llm_case(case: dict, mcp: MCPClient) -> tuple[bool, str]:
    try:
        result = await llm.answer_with_llm(case["question"], [], mcp)
    except APIError as e:
        # A transient Gemini-side error (e.g. 503 "high demand") shouldn't
        # crash the whole suite — score this one case as a failure and let
        # the rest run, same as main.py's /chat does for live traffic.
        return False, f"Gemini API error: {e}"
    if result.text is None:
        return False, "no answer returned (empty response)"

    expected_tools = case.get("expected_tool_calls")
    if expected_tools:
        missing = [t for t in expected_tools if t not in result.tool_calls]
        if missing:
            return False, f"expected tool call(s) {missing} not made (actual: {result.tool_calls})"

    return score_text(result.text, case)


async def run_all() -> list[CaseResult]:
    dataset = json.loads(DATASET_PATH.read_text())
    results: list[CaseResult] = []

    for case in dataset.get("router_cases", []):
        passed, detail = score_router_case(case)
        results.append(CaseResult("router", case["question"], passed, detail))

    mcp = MCPClient()
    await mcp.connect()
    try:
        for case in dataset.get("llm_fallback_cases", []):
            passed, detail = await score_llm_case(case, mcp)
            results.append(CaseResult("llm_fallback", case["question"], passed, detail))

        for case in dataset.get("adversarial_cases", []):
            passed, detail = await score_llm_case(case, mcp)
            results.append(CaseResult("adversarial", case["question"], passed, detail))
    finally:
        await mcp.cleanup()

    return results


def maybe_report_to_langfuse(results: list[CaseResult], score: float) -> None:
    """Push a named score for this run to Langfuse, if credentials are configured.

    Not a hard dependency: run_eval.py's pass/fail gate (the exit code) never
    depends on Langfuse being reachable — this is purely for dashboard
    visibility on top of the local, deterministic result computed above.
    """
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        print("\n(Langfuse credentials not set — skipping dataset run upload, local result above is authoritative)")
        return

    from langfuse import get_client

    client = get_client()
    trace_id = client.create_trace_id()
    with client.start_as_current_observation(trace_context={"trace_id": trace_id}, name="eval_run", as_type="span"):
        client.score_current_trace(name="eval_aggregate_score", value=score, data_type="NUMERIC")
        for r in results:
            client.score_current_trace(
                name=f"eval_case_{r.category}",
                value=r.passed,
                data_type="BOOLEAN",
                comment=f"{r.question!r}: {r.detail}",
            )
    client.flush()
    print(f"\nReported to Langfuse (trace {trace_id})")


def main() -> int:
    results = asyncio.run(run_all())

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] ({r.category}) {r.question!r} — {r.detail}")

    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    score = passed_count / total if total else 0.0

    print(f"\nAggregate: {passed_count}/{total} = {score:.1%} (threshold: {PASS_THRESHOLD:.0%})")

    maybe_report_to_langfuse(results, score)

    if score < PASS_THRESHOLD:
        print("\nREGRESSION: aggregate score is below the pass threshold.")
        return 1

    print("\nPASS: aggregate score meets the pass threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
