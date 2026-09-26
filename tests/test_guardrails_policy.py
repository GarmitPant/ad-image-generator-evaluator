from adgen.config import load_policy
from adgen.context import resolve_context
from adgen.contracts import Geography, Season
from adgen.planning import keyword_review

from .helpers import ROOT

POLICY = load_policy(ROOT / "policy/guardrails.yaml")
CONTEXT = resolve_context(Geography.AU, Season.summer)


def rules_hit(setting):
    plan = {"setting": setting, "avoid": [], "rationale": ""}
    return {r["rule_id"] for r in keyword_review(plan, CONTEXT, POLICY)}


def test_regional_style_and_background_landmarks_are_allowed():
    assert (
        rules_hit("Sydney harbour cafe, sandstone terrace, skyline and kangaroo paw flowers behind")
        == set()
    )


def test_flags_and_religious_sites_remain_banned():
    assert rules_hit("A bar with a flag on the wall") == {"GR-TOKEN"}
    assert rules_hit("Terrace facing a temple") == {"GR-RELIGION"}


def test_country_notes_invite_a_specific_region_for_every_country():
    for geography in Geography:
        assert (
            "specific city or region" in resolve_context(geography, Season.winter)["context_note"]
        )
