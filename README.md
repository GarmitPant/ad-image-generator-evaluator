# Ad image generator and evaluator

G2 hackathon project. **Generation, per-candidate evaluation, ranking and the submission report are implemented.** Generation has been verified live once (see `data/live-runs/`). The evaluator is tested on genuine recorded OCR/detection evidence; its judge has not yet been run live or calibrated against human labels. There is no UI.

## Run locally

Python 3.11+; macOS/Linux. From this repository:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
adgen state init
adgen demo
```

The demo costs nothing, needs no keys and creates clearly marked **synthetic placeholders**, not generated ads. Its output prints a run ID and export directory. SQLite is created automatically at `runs/state.db`; artifacts and exported PNGs are also under gitignored `runs/`.

```sh
pytest -q
ruff check src tests
```

The tests deny network connections, including when exercising real SDK serialization with mock HTTP transports. See the [implementation checkpoint](docs/implementation-status.md) and [generation runbook](docs/generation-runbook.md).

## Evaluate, rank and report

```sh
python -m pip install -e ".[eval]"   # local OCR/detector/embedder (~1.5 GB incl. weights; see runbook §7)
adgen generate --request REQUEST.json --mode live --allow-paid     # generate -> evaluate -> rank -> export best
adgen evaluate --request REQUEST.json --run-id RUN_ID --mode live --allow-paid   # score an existing run, no regeneration
adgen report --out submission                                       # submission bundle from all evaluated runs
```

Every candidate gets text-selection, text-rendering, product (same-object) and context verdicts plus ranking scores. The winner is `approved` only if it passes every required check. Exports include `best.png` and `evaluations/`. `adgen report` writes `report.md`, `results.csv/json`, `contact-sheet.html`, `images/`, `evidence/` and `requests.jsonl`, and compares automated verdicts with human labels in `data/labels.csv` (see `data/LABELS.md`). `--skip-evaluation` keeps generation-only behaviour. The demo and all tests run offline without the `[eval]` models.

## What is implemented

Input → validate/normalize 1–3 references → freeze Exact/Extract copy → resolve geography/season → analyze the product → for each candidate: plan → review/replan once → compile prompt → generate one Gemini image → validate/save → export every candidate as `generated_unscored`.

- 1–4 candidates, default 3, with a separate creative plan for each.
- OpenAI for product analysis, Extract selection, planning and the **pre-generation plan** review. Gemini for images.
- Planner sees text roles/lengths, not the supplied copy. Freeform text is content to display, not art direction.
- **Exact:** keep the source string, punctuation, case and line breaks. **Extract:** select exact source spans; protected phrases/spans must remain intact. Pilot capacity: 4 blocks, 120 non-whitespace characters and 20 whitespace-delimited words total.
- All references are passed to generation in declared order. Originals and normalized renditions are saved, hashed and linked.
- Static plan guardrails plus an LLM reviewer; one replan. A second rejected but valid plan is rendered with `rejected_after_replan`, as specified.
- SQLite lineage, per-call usage and report-only cost estimates, receipt persistence, immutable resume, exact-match replay and individual candidate failure isolation.
- Output validation checks image bytes, square aspect and size. It does **not** judge text accuracy, product fidelity or context correctness. Future evaluation must do that.

## Requests and provider configuration

Examples: [three-reference Exact](examples/heineken-exact.json), [single-reference Extract](examples/bottle-extract.json). Image paths resolve relative to the request JSON file. Geography: `US`, `GB`, `DE`, `JP`, `IN`, `AU`, `BR`, `AE`; season: `spring`, `summer`, `autumn`, `winter`.

Model IDs, efforts, timeouts and provisional cost estimates live in [config/pipeline.toml](config/pipeline.toml). Only `.env.example` with empty placeholders is committed. Copy it to `.env` and provide your own `OPENAI_API_KEY` and `GEMINI_API_KEY` when live testing is authorized. The current checkpoint is explicitly **offline only**.

A live call requires `--mode live --allow-paid`. There is no local spend cap. **Set spend limits on your OpenAI and Google accounts** (prepaid credit without auto-recharge, or project usage limits). Per-call usage and estimated cost are recorded for reporting only. The runbook has the live command, call counts, replay/resume instructions and limitations. No automatic provider retries are enabled.

## Design and next phase

1. [Review and implementation plan](docs/generation-implementation-plan.md)
2. [Generation design](docs/design/01-generation-pipeline.md)
3. [State-store design](docs/design/06-state-store.md)
4. [Evaluation and text contract — not yet implemented](docs/design/05-evaluation-and-text-contract.md)
5. [Implementation handoff](docs/design/04-implementation-handoff.md)
6. [Model decisions and sources](docs/design/02-model-decisions.md)

The eventual evaluator should assess source → selected-copy fidelity, selected-copy → rendered-text fidelity, product identity and independent geography/season criteria for every candidate. Only then add ranking and batch evaluation.

Reference photo provenance: [data/products](data/products/README.md). Original context came from `GarmitPant/resume-workbench` commit `b937bc4` and remains in `docs/context/`; it is historical. Read [AGENTS.md](AGENTS.md), [decisions](docs/decisions.md) and [collaboration record](docs/agent-collaboration.md) before continuing.
