# Ad image generator and evaluator

Generates display-ad images from a product photo, a target country, a season and free-form ad text. It then **automatically evaluates every generated image** and picks the best one. Built in Python for the G2 AI hackathon (problem 2: enrichment of image generation using structured context).

- **Generation:** Google Gemini 3.1 Flash Image renders the ads. OpenAI models analyse the product, choose the ad copy and plan each scene.
- **Evaluation:** every image is checked for text accuracy, product fidelity and context. Local vision models (OCR, object detection, image embeddings) do the measuring, and an **LLM-as-judge** (a multimodal OpenAI model that sees the reference photos and the ad) answers narrow yes/no questions. Pass or fail is always decided in code, never by the LLM.
- **Output:** a ranked set of candidates per request, the winning `best.png`, and a human-readable evaluation report with evidence for every image.

## How it works

```text
request (product photo(s) + country + season + ad text)
  │
  ├─ normalize reference photo(s)              code
  ├─ choose the ad copy                        Exact: whole text (code) · Extract: relevant excerpts (OpenAI, verified in code)
  ├─ analyse the product                       OpenAI vision → shape, colours, parts, branding
  ├─ resolve country + season                  code (hemisphere-aware months, climate)
  └─ for each of N candidates:
       ├─ plan the scene and layout            OpenAI (sees only the length and role of the copy, never its wording)
       ├─ check the plan against guardrails    keyword rules + OpenAI reviewer; one retry, then flag
       ├─ build the image prompt               code
       ├─ generate one image                   Gemini 3.1 Flash Image, 1:1, 1024 px
       └─ evaluate the image                   OCR + detector + embeddings (local) + LLM judge → verdicts
  │
  └─ rank candidates in code → best.png + evaluation records
```

### What the evaluator checks

Each image gets **PASS**, **FAIL** or **UNSURE** in four dimensions. It passes overall only if every required check passes. Missing or conflicting evidence gives UNSURE, never PASS.

| Dimension | Checks |
|---|---|
| Text selection (input → copy) | Copy is an exact excerpt of the input; protected phrases kept whole; fits the ad; in Extract mode, the LLM judge checks that meaning is preserved (no lost "not" or "up to") and nothing essential is dropped. A failure counts only if it quotes the input |
| Text rendering (copy → image) | OCR reads the image **without being told the expected text**. Every copy line must appear exactly once, spelled exactly, with no duplicated or extra ad text. Text printed on the product itself is ignored |
| Product | Exactly one product (detector and LLM judge must agree); the LLM judge compares type, shape, colours and materials, distinctive parts and branding with the reference photos. Position and viewing angle are not judged |
| Context | LLM judge: scene fits the season and is plausible for the country; no out-of-season elements; no flags, caricature, religious imagery or irresponsible alcohol depiction |

Candidates are ranked by: verdict → number of failed checks → score → whether the country is recognisable → visual similarity of the product to the reference → candidate number. Scores only break ties; a high score never outranks a failed check.

## Repository layout

```text
src/adgen/           pipeline, CLI and evaluator (src/adgen/eval/)
config/              pipeline.toml (models, timeouts, prices) · evaluator.toml (local models, thresholds)
policy/              guardrails.yaml: content rules applied to every country
data/products/       reference product photos with provenance (README inside)
data/requests/       example requests (batch-v1 = the evaluated set)
scripts/             run-batch.sh: run a folder of requests
submission/          generated evaluation report, results, images and evidence
tests/               offline test suite (no network, no API keys)
```

## Setup

Requires Python 3.11+ on macOS or Linux; tested on an Apple M1 with 8 GB of RAM.

```sh
git clone https://github.com/GarmitPant/ad-image-generator-evaluator.git
cd ad-image-generator-evaluator
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e ".[eval]"      # local evaluator models: torch, transformers, PaddleOCR (~1 GB)
```

Download the local model weights once (about 800 MB). At run time the evaluator loads them offline:

```sh
python - <<'EOF'
from huggingface_hub import snapshot_download
for repo, rev in [("IDEA-Research/grounding-dino-tiny", "a2bb814dd30d776dcf7e30523b00659f4f141c71"),
                  ("facebook/dinov2-small",            "ed25f3a31f01632728cabb09d1542f84ab7b0056")]:
    snapshot_download(repo, revision=rev, allow_patterns=["*.json", "*.txt", "model.safetensors"])
EOF
```

PaddleOCR downloads its own text models (about 100 MB) the first time it runs.

Add your own API keys. The repository contains only empty placeholders:

```sh
cp .env.example .env      # then fill in GEMINI_API_KEY and OPENAI_API_KEY
```

Live runs cost money, and **there is no spending cap in the code**. Set usage limits on your OpenAI and Google accounts. As a rough guide, one request with 3 candidates costs about $0.30–0.40 and takes 3–4 minutes.

## Run

**Offline demo (no keys, no cost).** Runs the whole pipeline with clearly labelled synthetic stand-ins for every model, so you can see the flow and the outputs:

```sh
adgen demo
```

**Generate, evaluate and rank one request:**

```sh
adgen generate --request data/requests/batch-v1/04-bottle-de-winter-extract.json --mode live --allow-paid
```

`--allow-paid` is required for any live call, as a guard against accidental spending. Add `--skip-evaluation` to generate without evaluating.

**Run a folder of requests.** Completed requests are skipped, so an interrupted batch can simply be re-run:

```sh
scripts/run-batch.sh data/requests/batch-v1
```

The script keeps its runs in `runs/batch-v1/state.db`.

**Re-score an existing run** with the current evaluator, without regenerating images:

```sh
adgen evaluate --request REQUEST.json --run-id RUN_ID --mode live --allow-paid
```

**Build the evaluation report** from all evaluated runs in a state database:

```sh
ADGEN_STATE_DB=runs/batch-v1/state.db adgen report --out submission
```

**Inspect a run:** `adgen state show RUN_ID`. **Export a run's images:** `adgen export RUN_ID`.

### Request format

```json
{
  "request_id": "bottle-de-winter",
  "product_images": ["../../products/water-bottle.jpg"],
  "geography": "DE",
  "season": "winter",
  "text": {
    "mode": "extract",
    "source_text": "Our insulated steel bottle keeps drinks hot for 12 hours and cold for 24 hours. Leak-proof lid. Not dishwasher safe.",
    "protected_phrases": ["Leak-proof lid."]
  },
  "n_candidates": 3,
  "aspect_ratio": "1:1"
}
```

| Field | Values |
|---|---|
| `product_images` | 1–3 photos of the **same** product (PNG/JPEG/WebP), paths relative to the request file |
| `geography` | `US`, `GB`, `DE`, `JP`, `IN`, `AU`, `BR`, `AE` |
| `season` | `spring`, `summer`, `autumn`, `winter`, as experienced in that country (Australian winter is June–August) |
| `text.mode` | `exact`: render the whole text as given · `extract`: pick the relevant parts, keeping any `protected_phrases` unchanged |
| `n_candidates` | 1–4 images to generate and rank (default 3) |

The text is treated as **content to display, never as instructions about the image**. For example, "winter sale" in the copy does not turn a summer scene into winter.

## Outputs

| Where | What |
|---|---|
| `runs/…/exports/<run_id>/` | `best.png`, every `candidate-NN.png`, `evaluations/` (one JSON record per candidate), `summary.json` (ranking), `text-plan.json` |
| `runs/…/state.db` | SQLite record of every stage, model call, cost estimate and artifact; runs can be resumed and inspected |
| `submission/report.md` | Evaluation report: summary, method, results per dimension, per-request rankings with reasons, limitations |
| `submission/contact-sheet.html` | All images with their verdicts (open in a browser) |
| `submission/evidence/*.md` | One readable card per image: every check with its reason, expected copy vs the text OCR actually read |
| `submission/results.csv`, `results.json` | One row per image; `results.json` and `evidence/*.json` hold the full detail |

`runs/` is local and gitignored.

## Tests

```sh
pytest -q            # offline; no API keys or local model weights needed
ruff check src tests
```

The tests use recorded real evidence (OCR and detections from generated ads) plus synthetic fixtures. They cover text matching, product and context composition, ranking, guardrails, crash-safe resume and replay. CI runs the same checks on every push.

## Configuration

- `config/pipeline.toml`: model IDs (`gpt-6-sol`, `gemini-3.1-flash-image`), reasoning effort, timeouts and list prices for cost estimates.
- `config/evaluator.toml`: pinned local models and evaluation thresholds. The thresholds are provisional.
- `policy/guardrails.yaml`: content rules. Stereotypes of people, flags and religious imagery are banned; regional architecture, materials, food and landscapes are encouraged so countries look distinct.

## Limitations

- The evaluator's judgments have not been validated against human labels. Its behaviour is tested on recorded real cases and constructed ones.
- OCR cannot read stylised logos, so product branding relies mainly on the LLM judge.
- Country-level context is an approximation. The evaluator checks for contradictions and plausibility, not a precise location.
- Only square 1024 px images are produced.

## Credits

Product photos are from Unsplash; see `data/products/README.md` for sources. Brand names shown in the photos belong to their owners, and the generated ads are research demonstrations only.
