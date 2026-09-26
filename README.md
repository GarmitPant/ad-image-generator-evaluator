# Ad image generator and evaluator

G2 hackathon project: generate contextual display ads and demonstrate a rigorous automated evaluator for content, product identity, scene context and rendered text.

**This repository holds specifications and implementation. Current status: design v0.3; implementation starting with the generation pipeline. No measured results yet.** See [implementation status](docs/implementation-status.md).

## Priority

The hackathon emphasizes engineering around evaluation methods, criteria, automated tests and trustworthy evidence. Implementation builds the generation pipeline first (LLM planner with general guardrails, one Gemini image per request, SQLite state store), then the evaluator. Best-of-N, repairs and UI are deferred.

## Providers and keys

OpenAI powers the LLM stages; Google Gemini generates images. Copy `.env.example` to `.env` and add your own `GEMINI_API_KEY` and `OPENAI_API_KEY`. No keys are committed. Offline tests need no keys.

## Text input

Freeform text supplies content to display, not visual art direction. Garmit confirmed two modes:

- **Exact:** preserve all supplied content, allowing only declared layout whitespace/reflow.
- **Extract:** select relevant source spans; optional protected phrases must remain unchanged. Freeze the selected copy before image generation.

Evaluate both **source → selected copy** (relevance, coverage, meaning and protected content) and **selected copy → rendered pixels** (accuracy, legibility and extra/missing text). A correct rendering of a bad extraction still fails end-to-end text fidelity.

## Read in order

1. [Generation pipeline](docs/design/01-generation-pipeline.md)
2. [State store](docs/design/06-state-store.md)
3. [Evaluation and text contract](docs/design/05-evaluation-and-text-contract.md)
4. [Implementation handoff](docs/design/04-implementation-handoff.md)
5. [Model decisions and sources](docs/design/02-model-decisions.md)
6. [Challenges and decisions](docs/design/03-challenges-and-decisions.md)

Reference product photos and their provenance: [data/products](data/products/README.md).

Read [AGENTS.md](AGENTS.md) before implementation. Record decisions in [docs/decisions.md](docs/decisions.md) and actual agent work in [docs/agent-collaboration.md](docs/agent-collaboration.md).

## Provenance

The original context is preserved in `docs/context/`, copied from `GarmitPant/resume-workbench` commit `b937bc4`. Garmit's subsequent clarification supersedes the historical blanket whole-input-verbatim rule and generation-first priority. Current contracts live in `docs/design/`; historical requirements are retained for accurate disclosure.
