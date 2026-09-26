# Guide for coding agents (and humans) working in this repository

This file is tool-agnostic: Claude Code, Codex, Cursor, Copilot and other agents can all follow it. Read `README.md` (what the project does, setup, commands) and `DESIGN.md` (why it is built this way) first.

## What this repository is

A Python pipeline that generates display-ad images (Gemini 3.1 Flash Image) from product photos, a country, a season and ad text, then **evaluates every image** with local vision models plus an LLM-as-judge (OpenAI), ranks the candidates in code and writes a human-readable report.

```text
src/adgen/
  cli.py            command-line entry point (adgen …)
  pipeline.py       orchestrates all stages over the state store
  contracts.py      request and model-output schemas (pydantic, extra fields forbidden)
  assets.py         image decoding, normalisation, hashing
  text.py           Exact/Extract copy selection and validation
  context.py        country facts and hemisphere-aware seasons
  planning.py       planner/reviewer prompts, plan validation, keyword guardrails, image prompt
  providers.py      OpenAI/Gemini adapters, record/replay, call ledger
  state/            SQLite state store and numbered migrations
  demo.py           synthetic provider for the offline demo and tests
  eval/             evaluator: vision.py (local models), text_eval.py, judge.py, evaluator.py,
                    compose.py (verdicts, scores, ranking), report.py (report bundle)
config/             pipeline.toml, evaluator.toml
policy/             guardrails.yaml
tests/              offline tests; tests/fixtures/ holds genuine recorded evidence
```

## Commands

```sh
source .venv/bin/activate
pytest -q                   # must pass before any commit; offline, no keys needed
ruff check src tests        # lint (line length 100)
ruff format src tests       # formatting
adgen demo                  # offline end-to-end smoke run with synthetic models
```

Live commands (`--mode live --allow-paid`) cost money. **Run them only with the repository owner's explicit approval.** Never add automatic retries around paid calls.

## Rules that keep the system correct

Break one of these only after an explicit decision by the owner, and update `DESIGN.md` when you do.

1. **Verdicts are composed in code.** Models return measurements (OCR text, boxes, similarity) or answers to narrow yes/no/unknown questions. Never let a model return an overall verdict or score. A failed required check fails; otherwise an unresolved one gives UNSURE. Missing evidence is never a pass.
2. **Keep the evaluator blind where it matters.** OCR and the LLM judge must never be given the expected ad copy, and judge prompts must never contain the answer that passes. Tests enforce this; keep them green.
3. **Ad text is content, not instructions.** The scene planner sees only the role and length of each copy block, never its wording. Never pass raw source text into scene planning or the image prompt except as literal copy to render.
4. **Scores only break ties.** Ranking is: verdict, failed checks, score, diagnostics, guardrail status, candidate index. A higher score must never outrank a failed check.
5. **Scene criteria come from inputs and policy.** The evaluator must never adopt the planner's own cues as pass criteria, because that would let the generator grade itself.
6. **Paid-call safety.** Every provider call is recorded as dispatched before it is sent. A call with an unknown outcome is never re-sent automatically. SDK retries stay disabled.
7. **No secrets anywhere.** Keys live only in `.env` (gitignored). Never log, print, store or commit them. Error records store exception type names, not SDK messages.

## Versioning: when you change behaviour, bump the version

Runs are content-addressed, so a changed prompt or criterion must not silently mix with earlier results.

| If you change… | Bump |
|---|---|
| Generation prompts, planner or reviewer instructions | `prompts` in `src/adgen/config.py` and `version` in `config/pipeline.toml` |
| Guardrail rules or keywords | `version` in `policy/guardrails.yaml` |
| Any evaluator check, question, threshold or local model | `version` in `config/evaluator.toml`. Evaluation stages are named after it, so existing runs can be re-scored with `adgen evaluate` without regenerating |
| The ranking rule | `RANKING_VERSION` in `src/adgen/eval/compose.py` (re-ranking reuses stored evaluations) |
| The database schema | Add a new numbered file in `src/adgen/state/migrations/` and append it to `MIGRATIONS`. Never edit an existing migration |

Comments in TOML/YAML files are not part of any config hash; the values are.

## Extending

- **Add a country:** add it to `Geography` in `src/adgen/contracts.py` and add one row to `FACTS` in `src/adgen/context.py` (name, hemisphere, climate band, neutral note). No per-country scene templates. The completeness tests cover every country × season.
- **Add an evaluator check:** add the question in `src/adgen/eval/judge.py` (or a code check in `text_eval.py` / `evaluator.py`), decide whether it is required or diagnostic (`DIAGNOSTIC`), give it a readable name in `CHECK_NAMES` (`src/adgen/eval/report.py`), add tests, and bump the evaluator version.
- **Add a product or request:** put photos in `data/products/` with source and licence in its README, and write a request JSON (format in `README.md`). Several references in one request must show the same product variant.

## Testing conventions

- Tests never touch the network: `tests/conftest.py` blocks sockets. Use `adgen.demo.SyntheticProvider`, `SyntheticVision`, or the record/replay backends.
- **Genuine recorded evidence** (real OCR/detections from generated ads) lives in `tests/fixtures/` and is labelled with its source. **Synthetic** responses test control flow only. Never present synthetic results as evidence of model quality.
- When a real run reveals an evaluator mistake, record that case as a fixture and add a regression test before fixing it.
- Offline tests must not need API keys or the local model weights. Import heavy libraries (torch, transformers, PaddleOCR) lazily inside functions.

## Working practices

- Stage explicit paths (`git add path …`), not `git add -A`, and review what you commit. Data files dropped into the tree by others must not be committed unreviewed.
- Do not change code or config while a batch is running. `scripts/run-batch.sh` starts a new process per request, so edits would affect the remaining requests.
- Keep `runs/` (local state, artifacts, exports) out of Git. Only curated results belong in the repository (`submission/`).
- Report honestly: counts beside percentages, unknowns and failures included, and no claims of evaluator accuracy without human-labelled evidence.
