import tomllib
from pathlib import Path

from pydantic import Field

from ..contracts import Contract


class EvaluatorConfig(Contract):
    version: str
    judge_effort: str
    ocr_det_model: str
    ocr_rec_model: str
    detector_model: str
    detector_revision: str
    embedder_model: str
    embedder_revision: str
    detector_box_threshold: float = Field(gt=0, lt=1)
    detector_text_threshold: float = Field(gt=0, lt=1)
    detector_count_threshold: float = Field(gt=0, lt=1)
    ocr_confident: float = Field(gt=0, le=1)
    ocr_noise: float = Field(ge=0, lt=1)
    line_merge_gap: float = Field(gt=0)
    min_text_height_px: int = Field(gt=0)
    max_block_lines: int = Field(ge=1, le=6)

    @classmethod
    def load(cls, path):
        return cls.model_validate(tomllib.loads(Path(path).read_text()))

    def models(self):
        """Model identity that keys recorded vision evidence."""
        return {
            "ocr": [self.ocr_det_model, self.ocr_rec_model],
            "detector": [self.detector_model, self.detector_revision],
            "embedder": [self.embedder_model, self.embedder_revision],
        }
