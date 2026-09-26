import base64
import io
import json

import httpx
import pytest
from google import genai
from google.genai import types
from openai import APIStatusError, OpenAI
from PIL import Image

from adgen.contracts import GuardrailReview
from adgen.providers import SYSTEM_INSTRUCTION, LiveProvider, estimate_cost


def png():
    output = io.BytesIO()
    Image.new("RGB", (20, 20), "red").save(output, format="PNG")
    return output.getvalue()


def invocation(kind="text"):
    return {
        "kind": kind,
        "purpose": "review" if kind == "text" else "image",
        "model": "model-under-test",
        "prompt": "Test prompt",
        "system": SYSTEM_INSTRUCTION,
        "schema": GuardrailReview.model_json_schema(),
        "effort": "low",
        "max_output_tokens": 4096,
    }


def test_openai_wire_payload_all_refs_strict_schema_and_usage(config):
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp-test",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": "model-returned",
                "output": [
                    {
                        "type": "message",
                        "id": "msg-test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"verdict":"approve","reasons":[]}',
                                "annotations": [],
                            }
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )

    client = OpenAI(
        api_key="offline-test-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = LiveProvider(config, openai_client=client).invoke(invocation(), [png(), png()])
    body = captured[0]
    assert body["store"] is False
    assert body["text"]["format"]["strict"] is True
    assert len(body["input"][1]["content"]) == 3
    assert all(
        p["image_url"].startswith("data:image/png;base64,") for p in body["input"][1]["content"][1:]
    )
    assert result.metadata["model_returned"] == "model-returned"
    assert result.metadata["usage"]["input_tokens"] == 10
    client.close()


def test_openai_sdk_does_not_retry(config):
    attempts = []

    def handler(request):
        attempts.append(1)
        return httpx.Response(
            500, json={"error": {"message": "offline simulated failure", "type": "server_error"}}
        )

    client = OpenAI(
        api_key="offline-test-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(APIStatusError):
        LiveProvider(config, openai_client=client).invoke(invocation(), [])
    assert len(attempts) == 1
    client.close()


def test_google_wire_payload_and_ignore_thought_image(config):
    captured = []
    image = base64.b64encode(png()).decode()

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "responseId": "google-test",
                "modelVersion": "model-returned",
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "thought": True,
                                    "inlineData": {"mimeType": "image/png", "data": image},
                                },
                                {"inlineData": {"mimeType": "image/png", "data": image}},
                            ],
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 20,
                    "candidatesTokenCount": 100,
                    "candidatesTokensDetails": [{"modality": "IMAGE", "tokenCount": 100}],
                },
            },
        )

    client = genai.Client(
        api_key="offline-test-key",
        http_options=types.HttpOptions(
            httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    result = LiveProvider(config, google_client=client).invoke(
        invocation("image"), [png(), png(), png()]
    )
    body = captured[0]
    parts = [p for content in body["contents"] for p in content["parts"]]
    assert sum("inlineData" in p for p in parts) == 3
    assert body["generationConfig"]["imageConfig"] == {"aspectRatio": "1:1", "imageSize": "1K"}
    assert (
        body["generationConfig"]["thinkingConfig"].get(
            "thinkingLevel", body["generationConfig"]["thinkingConfig"].get("thinking_level")
        )
        == "MINIMAL"
    ), body["generationConfig"]
    assert len(result.images) == 1
    assert result.metadata["error_code"] is None
    cost, unknown = estimate_cost(config, invocation("image"), result.metadata)
    assert cost > 0 and not unknown
    client.close()


def test_cost_estimate_is_report_only_and_unknown_without_usage(config):
    text = {"kind": "text"}
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000}
    cost, unknown = estimate_cost(config, text, {"usage": usage})
    assert cost == pytest.approx(3.0) and not unknown  # $2/M input + $10/M output
    assert estimate_cost(config, text, {"usage": None}) == (0.0, True)
    assert estimate_cost(config, {"kind": "image"}, {}) == (0.0, True)


@pytest.mark.parametrize(
    "parts,reason,expected",
    [
        ([], "SAFETY", "image_refused"),
        ([{"text": "No image"}], "STOP", "image_refused_or_missing"),
        (
            [{"inlineData": {"mimeType": "image/png", "data": base64.b64encode(png()).decode()}}]
            * 2,
            "STOP",
            "unexpected_multiple_images",
        ),
    ],
)
def test_google_nonimage_or_multiple_response_classification(config, parts, reason, expected):
    def handler(request):
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": parts}, "finishReason": reason}]}
        )

    client = genai.Client(
        api_key="offline-test-key",
        http_options=types.HttpOptions(
            httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    result = LiveProvider(config, google_client=client).invoke(invocation("image"), [])
    assert result.metadata["error_code"] == expected
    client.close()


def test_google_sdk_does_not_retry(config):
    attempts = []

    def handler(request):
        attempts.append(1)
        return httpx.Response(
            500, json={"error": {"code": 500, "message": "offline failure", "status": "INTERNAL"}}
        )

    client = genai.Client(
        api_key="offline-test-key",
        http_options=types.HttpOptions(
            httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    with pytest.raises(Exception):
        LiveProvider(config, google_client=client).invoke(invocation("image"), [])
    assert len(attempts) == 1
    client.close()
