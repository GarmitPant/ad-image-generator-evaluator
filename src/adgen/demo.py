"""Synthetic control-flow fixtures. Never evidence of model quality or API compatibility."""

import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

from .providers import ProviderResult, record_fixture
from .util import atomic_write, canonical


class SyntheticProvider:
    def __init__(self, fixture_dir=None):
        self.fixture_dir = fixture_dir
        self.calls = []

    def invoke(self, invocation, references):
        self.calls.append(invocation)
        purpose = invocation["purpose"]
        payload = (
            json.loads(invocation["prompt"].split("\nDATA:\n", 1)[1])
            if "\nDATA:\n" in invocation["prompt"]
            else {}
        )
        if purpose == "product_analysis":
            result = {
                "category": "synthetic demonstration bottle",
                "silhouette": "upright cylinder",
                "colors": ["teal"],
                "materials": ["unknown"],
                "distinctive_components": ["cap"],
                "visible_label_text": [],
                "unknowns": ["Synthetic fixture, not visual analysis"],
                "reference_inconsistencies": [],
                "age_restricted": False,
            }
        elif purpose == "extract":
            source = payload["source_text"]
            result = {
                "blocks": [{"start": 0, "end": len(source), "text": source, "role": "tagline"}]
            }
        elif purpose == "plan":
            zones = ["top_band", "bottom_left", "bottom_center", "bottom_right"]
            result = {
                "concept": "Synthetic control-flow demonstration",
                "setting": "A simple studio tabletop",
                "lighting": {"time_of_day": "day", "quality": "soft", "direction": "left"},
                "surface_and_props": ["plain tabletop"],
                "palette": ["teal", "white"],
                "people": "none",
                "product_placement": {
                    "zone": "middle_band",
                    "scale": 0.3,
                    "orientation": "upright",
                },
                "text_layout": [
                    {
                        "block_id": block["block_id"],
                        "zone": zones[i],
                        "size": "large",
                        "alignment": "center",
                        "type_style": "plain sans serif",
                        "contrast_treatment": "clean_background",
                    }
                    for i, block in enumerate(payload["text_blocks"])
                ],
                "context_cues": [
                    {
                        "cue": payload["resolved_context"]["country_name"]
                        + " contemporary tabletop setting",
                        "kind": "geography",
                    },
                    {
                        "cue": payload["resolved_context"]["season"] + " ambient daylight",
                        "kind": "season",
                    },
                ],
                "avoid": ["extra scene text"],
                "rationale": "Synthetic fixture only; not a real creative decision.",
            }
        elif purpose == "review":
            result = {"verdict": "approve", "reasons": []}
        elif purpose == "image":
            image = Image.new("RGB", (1024, 1024), "#e5f4f1")
            draw = ImageDraw.Draw(image)
            draw.rectangle((410, 290, 614, 770), fill="#19746b")
            draw.rectangle((450, 230, 574, 290), fill="#183b36")
            draw.text((70, 80), "SYNTHETIC FIXTURE - NOT MODEL OUTPUT", fill="black", font_size=30)
            draw.text(
                (70, 900),
                "Control-flow test only. No visual quality claim.",
                fill="black",
                font_size=25,
            )
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            response = ProviderResult(
                images=[buf.getvalue()],
                metadata={
                    "provenance": "synthetic",
                    "model_returned": "synthetic-fixture",
                    "usage": None,
                    "error_code": None,
                },
            )
        else:
            raise ValueError("unknown synthetic purpose")
        if purpose != "image":
            response = ProviderResult(
                text=canonical(result).decode(),
                metadata={
                    "provenance": "synthetic",
                    "model_returned": "synthetic-fixture",
                    "usage": None,
                    "error_code": None,
                },
            )
        if self.fixture_dir:
            record_fixture(self.fixture_dir, invocation, response)
        return response


def prepare_demo(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (128, 128), "#19746b")
    image.save(directory / "reference.png")
    request = {
        "request_id": "synthetic-demo",
        "product_images": ["reference.png"],
        "geography": "IN",
        "season": "summer",
        "text": {"mode": "exact", "source_text": "Stay refreshed"},
        "n_candidates": 3,
        "aspect_ratio": "1:1",
    }
    atomic_write(directory / "request.json", canonical(request))
    return directory / "request.json"
