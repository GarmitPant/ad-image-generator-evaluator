import tomllib
from pathlib import Path

import yaml
from pydantic import Field

from .contracts import Contract
from .util import fingerprint


class PipelineConfig(Contract):
    version: str
    llm_model: str
    image_model: str
    analysis_effort: str
    extract_effort: str
    planner_effort: str
    review_effort: str
    llm_timeout_seconds: float = Field(gt=0)
    image_timeout_seconds: float = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    image_max_output_tokens: int = Field(gt=0)
    max_llm_input_chars: int = Field(gt=0)
    openai_input_per_million: float = Field(ge=0)
    openai_output_per_million: float = Field(ge=0)
    google_input_per_million: float = Field(ge=0)
    google_text_output_per_million: float = Field(ge=0)
    google_image_output_per_million: float = Field(ge=0)
    pricing_version: str

    @classmethod
    def load(cls, path):
        return cls.model_validate(tomllib.loads(Path(path).read_text()))


def load_policy(path):
    policy = yaml.safe_load(Path(path).read_text())
    if not isinstance(policy, dict) or not all(
        k in policy for k in ("version", "global_rules", "keywords", "country_notes")
    ):
        raise ValueError("invalid guardrail policy")
    return policy


def config_hash(config, policy):
    return fingerprint(
        {
            "config": config.model_dump(),
            "policy": policy,
            "contracts": "generation/1",
            "prompts": "generation/1",
        }
    )
