"""Deterministic itinerary/booking checks for the eval harness.

Pure functions over the produced state - no LLM. These are the objective half of
the eval (the LLM-as-judge in judge.py is the subjective half).
"""

from __future__ import annotations

from dataclasses import dataclass

_PACKED_TRAVEL_MIN = 150.0  # matches the logistics threshold


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    score: float  # 0..1


def budget_respected(itinerary: dict, brief: dict) -> CheckResult:
    total = 0.0
    for d in itinerary.get("days", []):
        for it in d.get("items", []):
            total += it.get("cost_estimate") or 0.0
    budget = (brief.get("budget") or {}).get("total")
    if not budget:
        return CheckResult("budget_respected", True, "no budget set", 1.0)
    ok = total <= budget * 1.1  # 10% grace
    return CheckResult(
        "budget_respected", ok, f"estimated {total:.0f} vs budget {budget:.0f}", 1.0 if ok else 0.0
    )


def timing_feasible(itinerary: dict) -> CheckResult:
    bad = []
    for d in itinerary.get("days", []):
        if (d.get("travel_min") or 0) > _PACKED_TRAVEL_MIN:
            bad.append(d.get("day"))
    ok = not bad
    return CheckResult(
        "timing_feasible", ok, "all days walkable" if ok else f"over-packed days: {bad}", 1.0 if ok else 0.5
    )


def no_double_booking(confirmed: list[dict]) -> CheckResult:
    seen = set()
    dupes = []
    refs = set()
    for b in confirmed:
        if b.get("status") == "cancelled":
            continue
        key = (b.get("type"), b.get("title"))
        if key in seen:
            dupes.append(b.get("title"))
        seen.add(key)
        ref = b.get("booking_ref")
        if ref and ref in refs:
            dupes.append(ref)
        if ref:
            refs.add(ref)
    ok = not dupes
    return CheckResult("no_double_booking", ok, "no duplicates" if ok else f"duplicates: {dupes}", 1.0 if ok else 0.0)


def grounded_in_real_pois(itinerary: dict, pois: list[dict]) -> CheckResult:
    names = {p.get("name", "").lower() for p in pois}
    if not names:
        return CheckResult("grounded_in_real_pois", True, "no POI reference set", 1.0)
    items = [it for d in itinerary.get("days", []) for it in d.get("items", []) if it.get("geo")]
    if not items:
        return CheckResult("grounded_in_real_pois", False, "no geo-located items", 0.0)
    matched = sum(1 for it in items if it.get("title", "").lower() in names)
    frac = matched / len(items)
    return CheckResult(
        "grounded_in_real_pois", frac >= 0.5, f"{matched}/{len(items)} items match real POIs", round(frac, 2)
    )


def run_deterministic_checks(state: dict, pois: list[dict] | None = None) -> list[CheckResult]:
    itinerary = state.get("itinerary") or {}
    brief = state.get("trip_brief") or {}
    confirmed = state.get("confirmed_bookings") or []
    results = [
        budget_respected(itinerary, brief),
        timing_feasible(itinerary),
        no_double_booking(confirmed),
    ]
    if pois is not None:
        results.append(grounded_in_real_pois(itinerary, pois))
    return results
