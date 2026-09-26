# Ad image generator and evaluator

G2 hackathon project: generate contextual display ads and demonstrate a rigorous automated evaluator for content, product identity, scene context and rendered text.

**This repository holds specifications and implementation. Current status: specs only; no measured evaluation results yet.** Another coding agent implements here; this collaboration develops and reviews the design.

## Priority

The hackathon emphasizes engineering around evaluation methods, criteria, automated tests and trustworthy evidence. Generation needs to function. Start with one generated image per request; defer aesthetic planning, best-of-N, repairs and UI until evaluator validation is complete.

## Text input

Freeform text supplies content to display, not visual art direction. Garmit confirmed two modes:

- **Exact:** preserve all supplied content, allowing only declared layout whitespace/reflow.
- **Extract:** select relevant source spans; optional protected phrases must remain unchanged. Freeze the selected copy before image generation.

Evaluate both **source → selected copy** (relevance, coverage, meaning and protected content) and **selected copy → rendered pixels** (accuracy, legibility and extra/missing text). A correct rendering of a bad extraction still fails end-to-end text fidelity.

## Read in order

1. [Evaluation and text contract](docs/design/05-evaluation-and-text-contract.md)
2. [Functional generation baseline](docs/design/01-generation-pipeline.md)
3. [Implementation handoff](docs/design/04-implementation-handoff.md)
4. [Model decisions and sources](docs/design/02-model-decisions.md)
5. [Challenges and decisions](docs/design/03-challenges-and-decisions.md)

Read [AGENTS.md](AGENTS.md) before implementation. Record decisions in [docs/decisions.md](docs/decisions.md) and actual agent work in [docs/agent-collaboration.md](docs/agent-collaboration.md).

## Provenance

The original context is preserved in `docs/context/`, copied from `GarmitPant/resume-workbench` commit `b937bc4`. Garmit's subsequent clarification supersedes the historical blanket whole-input-verbatim rule and generation-first priority. Current contracts live in `docs/design/`; historical requirements are retained for accurate disclosure.
