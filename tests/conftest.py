import socket
from pathlib import Path

import pytest
from PIL import Image

from adgen.config import PipelineConfig, load_policy
from adgen.contracts import AdRequest
from adgen.demo import SyntheticProvider
from adgen.pipeline import Pipeline
from adgen.state import State

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Network is forbidden in offline tests")

    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(socket, "create_connection", fail)


@pytest.fixture
def config():
    return PipelineConfig.load(ROOT / "config/pipeline.toml")


@pytest.fixture
def policy():
    return load_policy(ROOT / "policy/guardrails.yaml")


@pytest.fixture
def state(tmp_path):
    value = State(tmp_path / "runs/state.db")
    yield value
    value.close()


@pytest.fixture
def request_data(tmp_path):
    for index in range(1, 4):
        Image.new("RGB", (64 + index, 80), (10 * index, 100, 200)).save(
            tmp_path / f"ref{index}.png"
        )
    return {
        "request_id": "test",
        "product_images": ["ref1.png"],
        "geography": "AU",
        "season": "summer",
        "text": {"mode": "exact", "source_text": "Fresh every day"},
        "n_candidates": 2,
    }


@pytest.fixture
def run_pipeline(state, config, policy, request_data, tmp_path):
    def run(backend=None, data=None, **kwargs):
        backend = backend or SyntheticProvider()
        pipe = Pipeline(state, config, policy, backend, kwargs.pop("mode", "replay"))
        result = pipe.run(AdRequest.model_validate(data or request_data), tmp_path, **kwargs)
        return result, backend

    return run
