"""Local vision evidence (OCR, detection, embeddings) behind one recorded interface.

Every result is stored as a content-addressed ``vision_evidence`` artifact keyed by operation,
input image hash, parameters and pinned model identity, so evaluations replay offline.
"""

import io
import json
import os
import tempfile
from pathlib import Path

from PIL import Image

from ..state import Blocked
from ..util import canonical, digest, fingerprint

OPS = {"ocr", "detect", "embed"}


def to_image(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as image:
        return image.convert("RGB")


def png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class VisionGateway:
    def __init__(self, state, backend, config):
        self.state, self.backend, self.config = state, backend, config

    def run(self, exec_id, op, image: bytes, params=None):
        if op not in OPS:
            raise ValueError("unknown vision operation")
        params = params or {}
        request = {
            "op": op,
            "image_sha256": digest(image),
            "params": params,
            "models": self.config.models(),
        }
        key = fingerprint(request)
        result = self.backend.run(key, op, image, params)
        record = {
            "key": key,
            "request": request,
            "result": result,
            "provenance": self.backend.provenance,
        }
        sha = self.state.artifact(canonical(record), "vision_evidence", "model")
        self.state.link(exec_id, sha, "output", f"vision:{key}")
        return result


def export_vision_fixtures(state, executions, directory):
    count = 0
    for exec_id in sorted(executions):
        for row in state.rows(
            "SELECT sa.artifact_id FROM stage_artifact sa JOIN artifact a USING(artifact_id) "
            "WHERE sa.exec_id=? AND sa.direction='output' AND a.kind='vision_evidence'",
            (exec_id,),
        ):
            record = state.json(row["artifact_id"])
            path = Path(directory) / "vision" / f"{record['key']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical(record))
            count += 1
    return count


class ReplayVision:
    provenance = "replay"

    def __init__(self, directory):
        self.directory = Path(directory) / "vision"

    def run(self, key, op, image, params):
        path = self.directory / f"{key}.json"
        if not path.is_file():
            raise Blocked("vision_fixture_missing")
        record = json.loads(path.read_text())
        if record.get("key") != key:
            raise Blocked("vision_fixture_mismatch")
        return record["result"]


class SyntheticVision:
    """Deterministic control-flow fixture. Not evidence of model quality."""

    provenance = "synthetic"

    def __init__(self, ocr_lines=(), detections=None, vector=(1.0, 0.0, 0.0)):
        self.ocr_lines = [{"text": t, "score": s, "box": list(b)} for t, s, b in ocr_lines]
        self.detections = (
            [{"score": 0.95, "box": [300, 300, 700, 700]}] if detections is None else detections
        )
        self.vector = list(vector)

    def run(self, key, op, image, params):
        if op == "ocr":
            return {"lines": self.ocr_lines}
        if op == "detect":
            return {"boxes": self.detections}
        return {"vector": self.vector}


class LocalVision:
    """PaddleOCR + Grounding DINO + DINOv2 on CPU, offline, loaded lazily one at a time."""

    provenance = "local"

    def __init__(self, config):
        self.config = config
        self._ocr = self._detector = self._embedder = None

    def run(self, key, op, image, params):
        return getattr(self, "_" + op + "_run")(image, params)

    def _ocr_run(self, image, params):
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                text_detection_model_name=self.config.ocr_det_model,
                text_recognition_model_name=self.config.ocr_rec_model,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        with tempfile.NamedTemporaryFile(suffix=".png") as handle:
            handle.write(png(to_image(image)))
            handle.flush()
            result = list(self._ocr.predict(handle.name))[0]
        return {
            "lines": [
                {"text": text, "score": round(float(score), 4), "box": [int(v) for v in box]}
                for text, score, box in zip(
                    result["rec_texts"], result["rec_scores"], result["rec_boxes"]
                )
            ]
        }

    def _load_hf(self, loader, processor, model, revision):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        kwargs = {"revision": revision, "local_files_only": True}
        return processor.from_pretrained(model, **kwargs), loader.from_pretrained(
            model, **kwargs
        ).eval()

    def _detect_run(self, image, params):
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        if self._detector is None:
            self._detector = self._load_hf(
                AutoModelForZeroShotObjectDetection,
                AutoProcessor,
                self.config.detector_model,
                self.config.detector_revision,
            )
        processor, model = self._detector
        picture = to_image(image)
        with torch.no_grad():
            inputs = processor(images=picture, text=params["label"], return_tensors="pt")
            output = model(**inputs)
        result = processor.post_process_grounded_object_detection(
            output,
            inputs.input_ids,
            threshold=self.config.detector_box_threshold,
            text_threshold=self.config.detector_text_threshold,
            target_sizes=[picture.size[::-1]],
        )[0]
        return {
            "boxes": [
                {"score": round(float(s), 4), "box": [int(v) for v in b.tolist()]}
                for s, b in zip(result["scores"], result["boxes"])
            ]
        }

    def _embed_run(self, image, params):
        import torch
        from transformers import AutoImageProcessor, AutoModel

        if self._embedder is None:
            self._embedder = self._load_hf(
                AutoModel,
                AutoImageProcessor,
                self.config.embedder_model,
                self.config.embedder_revision,
            )
        processor, model = self._embedder
        with torch.no_grad():
            vector = model(**processor(images=to_image(image), return_tensors="pt")).pooler_output[
                0
            ]
        vector = vector / vector.norm()
        return {"vector": [round(float(v), 6) for v in vector]}
