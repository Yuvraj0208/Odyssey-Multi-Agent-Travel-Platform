"""Eval harness. Runs golden scenarios end-to-end through the graph, then scores
each with deterministic checks + the LLM judge.

    python -m odyssey.evals.run

Deterministic mode (fixed seeds, canned mock providers) keeps booking scenarios
reproducible; the LLM-driven planning still needs a configured provider.
"""

from __future__ import annotations

import asyncio
import uuid

from langchain_core.messages import HumanMessage

from odyssey.evals.checks import run_deterministic_checks
from odyssey.evals.judge import judge_itinerary
from odyssey.graph.runtime import get_runtime, shutdown_runtime

GOLDEN = [
    {
        "id": "kyoto-relaxed",
        "text": "Plan a relaxed 3-day trip to Kyoto. I love temples and gardens. Budget 900 USD.",
    },
    {
        "id": "lisbon-foodie",
        "text": "4 days in Lisbon, foodie and history focused, walkable. Budget 1200 USD.",
    },
]


async def _run_scenario(runtime, scenario: dict) -> dict:
    session_id = f"eval_{scenario['id']}_{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": session_id}}
    inputs = {
        "messages": [HumanMessage(content=scenario["text"])],
        "user_id": "evaluator",
        "session_id": session_id,
        "active_agent": "supervisor",
        "next_agent": None,
        "hops": 0,
    }
    await runtime.graph.ainvoke(inputs, config=config)
    snapshot = await runtime.graph.aget_state(config)
    state = snapshot.values or {}
    pois = (state.get("context") or {}).get("pois") or []

    checks = run_deterministic_checks(state, pois)
    det_score = sum(c.score for c in checks) / max(1, len(checks))
    judge = await judge_itinerary(state.get("trip_brief") or {}, state.get("itinerary") or {})

    return {
        "id": scenario["id"],
        "deterministic": {c.name: {"passed": c.passed, "detail": c.detail, "score": c.score} for c in checks},
        "deterministic_score": round(det_score, 2),
        "judge": judge.model_dump() if judge else None,
    }


async def main() -> None:
    runtime = await get_runtime()
    print("Running", len(GOLDEN), "golden scenarios...\n")
    try:
        for sc in GOLDEN:
            try:
                report = await _run_scenario(runtime, sc)
            except Exception as e:
                print(f"[{sc['id']}] FAILED: {e}\n")
                continue
            print(f"=== {report['id']} ===")
            for name, r in report["deterministic"].items():
                mark = "PASS" if r["passed"] else "FAIL"
                print(f"  [{mark}] {name}: {r['detail']} (score {r['score']})")
            print(f"  deterministic score: {report['deterministic_score']}")
            if report["judge"]:
                j = report["judge"]
                print(f"  judge: overall {j['overall']}/5 - {j['comment']}")
            print()
    finally:
        await shutdown_runtime()


if __name__ == "__main__":
    asyncio.run(main())
