# Ad image generator and evaluator

G2 hackathon: generate contextual display ads from a product photo, target geography, season and required text; evaluate product fidelity, context adherence and text fidelity.

**Status: design and specification. No implementation or measured results yet.**

## Start here

- [Design pack](docs/design/README.md)
- [Image generation pipeline](docs/design/01-generation-pipeline.md)
- [Model choices and research](docs/design/02-model-decisions.md)
- [Challenges and proposed decisions](docs/design/03-challenges-and-decisions.md)
- [Implementation handoff](docs/design/04-implementation-handoff.md)
- [Original organizer statement and requirements](docs/context/01-problem-statement.md)

The proposed pipeline separates product analysis, structured ad planning, prompt compilation, Gemini image generation, and evaluation. The supplied ad copy stays verbatim. Python and CLI/library support come first; UI comes later.

Read [AGENTS.md](AGENTS.md) before implementation. Design proposals are explicitly distinguished from organizer requirements and Garmit's decisions. API billing, product photos, evaluator calibration and live model compatibility still need setup or validation.

## Collaboration and provenance

Original context came from `GarmitPant/resume-workbench`, commit `b937bc4`, under `hackathons/g2-ad-imagegen/`. It is preserved in `docs/context/`. Current proposals live in `docs/design/`; the originals are historical context, not instructions to override newer requirements.

Record implementation milestones in [the collaboration log](docs/agent-collaboration.md) and accepted decisions in [the decision register](docs/decisions.md). The hackathon requires an accurate coding-agent disclosure.
