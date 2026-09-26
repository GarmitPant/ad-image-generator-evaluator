"""Versioned, closed contracts. String offsets are Python Unicode codepoints."""

import re
import unicodedata
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Geography(str, Enum):
    US = "US"
    GB = "GB"
    DE = "DE"
    JP = "JP"
    IN = "IN"
    AU = "AU"
    BR = "BR"
    AE = "AE"


class Season(str, Enum):
    spring = "spring"
    summer = "summer"
    autumn = "autumn"
    winter = "winter"


class Span(Contract):
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("span must be nonempty and half-open")
        return self


class TextInput(Contract):
    mode: Literal["exact", "extract"]
    source_text: str = Field(min_length=1, max_length=2000)
    protected_phrases: list[str] = Field(default_factory=list, max_length=20)
    protected_spans: list[Span] = Field(default_factory=list, max_length=40)

    @field_validator("source_text")
    @classmethod
    def safe_text(cls, value):
        if not value.strip():
            raise ValueError("source text must have visible content")
        if any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} and c not in "\n\r\t" for c in value):
            raise ValueError("source contains unsupported control characters")
        return value


class AdRequest(Contract):
    request_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    product_images: list[str] = Field(min_length=1, max_length=3)
    geography: Geography
    season: Season
    text: TextInput
    n_candidates: int = Field(default=3, ge=1, le=4)
    aspect_ratio: Literal["1:1"] = "1:1"


Role = Literal["product_name", "tagline", "offer", "qualifier", "supporting_text"]


class TextBlock(Span):
    text: str
    role: Role


class CopySelection(Contract):
    blocks: list[TextBlock] = Field(min_length=1, max_length=4)


class ProductProfile(Contract):
    category: str
    silhouette: str
    colors: list[str]
    materials: list[str]
    distinctive_components: list[str]
    visible_label_text: list[str]
    unknowns: list[str]
    reference_inconsistencies: list[str]
    age_restricted: bool


# Layout zones on a 3x3 grid (cells 0-8, row-major). The single source for both the
# schema enum and overlap checks; key order is the enum order sent to the planner.
ZONE_CELLS = {
    **{
        f"{vertical}_{horizontal}": {row * 3 + col}
        for row, vertical in enumerate(("top", "middle", "bottom"))
        for col, horizontal in enumerate(("left", "center", "right"))
    },
    "top_band": {0, 1, 2},
    "middle_band": {3, 4, 5},
    "bottom_band": {6, 7, 8},
    "left_third": {0, 3, 6},
    "center_third": {1, 4, 7},
    "right_third": {2, 5, 8},
}
Zone = Literal[tuple(ZONE_CELLS)]


class Lighting(Contract):
    time_of_day: str = Field(max_length=60)
    quality: str = Field(max_length=100)
    direction: str = Field(max_length=60)


class ProductPlacement(Contract):
    zone: Zone
    scale: float = Field(ge=0.25, le=0.7)
    orientation: str = Field(max_length=100)


class TextLayout(Contract):
    block_id: str
    zone: Zone
    size: Literal["large", "medium", "small"]
    alignment: Literal["left", "center", "right"]
    type_style: str = Field(max_length=60)
    contrast_treatment: Literal["clean_background", "solid_panel", "gradient_scrim"]


class ContextCue(Contract):
    cue: str = Field(max_length=150)
    kind: Literal["geography", "season"]


class CreativePlan(Contract):
    concept: str = Field(max_length=120)
    setting: str = Field(max_length=300)
    lighting: Lighting
    surface_and_props: list[str] = Field(max_length=5)
    palette: list[str] = Field(max_length=5)
    people: Literal["none", "background_non_identifiable"]
    product_placement: ProductPlacement
    text_layout: list[TextLayout] = Field(min_length=1, max_length=4)
    context_cues: list[ContextCue] = Field(min_length=2, max_length=6)
    avoid: list[str] = Field(max_length=8)
    rationale: str = Field(max_length=1000)


class ReviewReason(Contract):
    rule_id: str
    explanation: str


class GuardrailReview(Contract):
    verdict: Literal["approve", "reject"]
    reasons: list[ReviewReason]

    @model_validator(mode="after")
    def consistent(self):
        if (self.verdict == "approve") != (len(self.reasons) == 0):
            raise ValueError("approval requires no reasons; rejection requires reasons")
        return self


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))
