import pytest

from adgen.eval.config import EvaluatorConfig
from adgen.eval.vision import ReplayVision, SyntheticVision, VisionGateway, export_vision_fixtures
from adgen.state import Blocked

from .helpers import ROOT, open_exec


def test_vision_evidence_recorded_exported_and_replayed(state, tmp_path):
    config = EvaluatorConfig.load(ROOT / "config/evaluator.toml")
    exec_id = open_exec(state)
    backend = SyntheticVision(ocr_lines=[("Fresh", 0.99, (10, 10, 90, 40))])
    recorded = VisionGateway(state, backend, config).run(exec_id, "ocr", b"image-bytes")
    assert export_vision_fixtures(state, [exec_id], tmp_path) == 1
    replayed = VisionGateway(state, ReplayVision(tmp_path), config).run(
        exec_id, "ocr", b"image-bytes"
    )
    assert replayed == recorded
    with pytest.raises(Blocked, match="vision_fixture_missing"):
        VisionGateway(state, ReplayVision(tmp_path), config).run(exec_id, "ocr", b"other")


def test_vision_key_depends_on_pinned_models(state, tmp_path):
    config = EvaluatorConfig.load(ROOT / "config/evaluator.toml")
    exec_id = open_exec(state)
    VisionGateway(state, SyntheticVision(), config).run(exec_id, "embed", b"x")
    export_vision_fixtures(state, [exec_id], tmp_path)
    changed = config.model_copy(update={"embedder_revision": "different"})
    with pytest.raises(Blocked, match="missing"):
        VisionGateway(state, ReplayVision(tmp_path), changed).run(exec_id, "embed", b"x")
