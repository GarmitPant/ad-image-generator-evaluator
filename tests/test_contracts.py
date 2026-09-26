import pytest
from pydantic import ValidationError

from adgen.context import resolve_context
from adgen.contracts import CopySelection, Geography, Season, TextInput
from adgen.text import exact_selection, freeze_selection, source_contract, text_shape


@pytest.mark.parametrize("geo", list(Geography))
@pytest.mark.parametrize("season", list(Season))
def test_all_geography_season_pairs(geo, season):
    context = resolve_context(geo, season)
    assert context["season"] == season.value
    assert len(context["months"]) == 3
    if geo in {Geography.AU, Geography.BR} and season == Season.summer:
        assert context["months"] == [12, 1, 2]
    if geo in {Geography.IN, Geography.BR, Geography.AE} or season == Season.summer:
        assert "snow" in context["avoid_terms"]


def test_exact_preserves_unicode_punctuation_and_linebreaks():
    source = "Café ☕\n東京 — 20% off!"
    contract = source_contract(TextInput(mode="exact", source_text=source))
    plan = freeze_selection(contract, exact_selection(contract))
    assert plan["blocks"][0]["text"] == source
    assert plan["blocks"][0]["end"] == len(source)
    assert plan["omissions"] == []
    assert source not in str(text_shape(plan))


def test_extract_spans_and_repeated_protection():
    source = "Sale now. Terms apply. Sale now."
    contract = source_contract(
        TextInput(mode="extract", source_text=source, protected_phrases=["Sale now."])
    )
    assert len(contract["protected_spans"]) == 2
    selection = CopySelection.model_validate(
        {
            "blocks": [
                {"start": 0, "end": 9, "text": source[:9], "role": "offer"},
                {"start": 23, "end": 32, "text": source[23:32], "role": "offer"},
            ]
        }
    )
    # Check offsets carefully: last span actually begins at 23 and ends at 32.
    assert len(source) == 32
    plan = freeze_selection(contract, selection)
    assert plan["omissions"][0]["text"] == source[9:23]
    assert not plan["semantics_evaluated"]


@pytest.mark.parametrize(
    "blocks",
    [
        [{"start": 0, "end": 3, "text": "BAD", "role": "tagline"}],
        [{"start": 0, "end": 99, "text": "abc", "role": "tagline"}],
        [
            {"start": 2, "end": 4, "text": "cd", "role": "tagline"},
            {"start": 1, "end": 3, "text": "bc", "role": "tagline"},
        ],
    ],
)
def test_invalid_extracted_spans(blocks):
    contract = source_contract(TextInput(mode="extract", source_text="abcdef"))
    with pytest.raises(ValueError):
        freeze_selection(contract, CopySelection.model_validate({"blocks": blocks}))


def test_protected_phrase_cannot_be_split_or_omitted():
    contract = source_contract(
        TextInput(mode="extract", source_text="Terms apply", protected_phrases=["Terms apply"])
    )
    with pytest.raises(ValueError, match="protected"):
        freeze_selection(
            contract,
            CopySelection.model_validate(
                {"blocks": [{"start": 0, "end": 5, "text": "Terms", "role": "qualifier"}]}
            ),
        )


@pytest.mark.parametrize("source", ["a" * 121, "one " * 21])
def test_capacity_fails_closed(source):
    contract = source_contract(TextInput(mode="exact", source_text=source))
    with pytest.raises(ValueError, match="capacity"):
        freeze_selection(contract, exact_selection(contract))


@pytest.mark.parametrize("source", ["", "   ", "abc\x00", "abc\u202e", "abc\ud800"])
def test_invalid_source(source):
    with pytest.raises(ValidationError):
        TextInput(mode="exact", source_text=source)


def test_absent_protected_phrase_and_out_of_bounds_span():
    with pytest.raises(ValueError):
        source_contract(TextInput(mode="extract", source_text="abc", protected_phrases=["missing"]))
    with pytest.raises(ValueError):
        source_contract(
            TextInput(mode="extract", source_text="abc", protected_spans=[{"start": 2, "end": 8}])
        )
