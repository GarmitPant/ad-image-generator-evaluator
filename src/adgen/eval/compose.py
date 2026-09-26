"""Verdicts are composed in code: a trusted failure fails, else an unresolved check is unknown."""

POINTS = {"pass": 1.0, "unknown": 0.5, "fail": 0.0}
TIERS = {"pass": 0, "unknown": 1, "fail": 2, None: 3}
GUARDRAIL_ORDER = {"approved": 0, "approved_after_replan": 1, "rejected_after_replan": 2, None: 3}
RANKING_RULE = (
    "ranking/1: verdict tier > failed required checks > overall score > guardrail > index"
)


def check(check_id, verdict, reason="", required=True, **evidence):
    assert verdict in POINTS, verdict
    return {
        "id": check_id,
        "verdict": verdict,
        "required": required,
        "reason": reason,
        "evidence": evidence,
    }


def compose(checks):
    required = [c["verdict"] for c in checks if c["required"]]
    if "fail" in required:
        return "fail"
    return "pass" if required and "unknown" not in required else "unknown"


def check_score(checks):
    required = [POINTS[c["verdict"]] for c in checks if c["required"]]
    return round(sum(required) / len(required), 4) if required else 0.5


def dimension(checks, score=None):
    return {
        "verdict": compose(checks),
        "score": check_score(checks) if score is None else round(score, 4),
        "checks": checks,
    }


def rank(records):
    """records: [{candidate_index, guardrail_status, evaluation|None}] -> ordered copy (best first)."""

    def key(item):
        ev = item.get("evaluation")
        if not ev:
            return (
                TIERS[None],
                99,
                0,
                GUARDRAIL_ORDER.get(item.get("guardrail_status"), 3),
                item["candidate_index"],
            )
        return (
            TIERS[ev["overall_verdict"]],
            ev["failed_required_checks"],
            -ev["overall_score"],
            GUARDRAIL_ORDER.get(item.get("guardrail_status"), 3),
            item["candidate_index"],
        )

    return sorted(records, key=key)
