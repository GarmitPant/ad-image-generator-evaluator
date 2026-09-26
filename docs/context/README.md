# G2 AI Hiring Hackathon — Problem 2: context-enriched ad image generation

Context bank for the G2 AI Engineer hackathon (Bengaluru), Problem statement 2, *"Enrichment
of image generation using structured context"*. Written 2026-09-26, the day before the event.
The work is **defining, scoping and researching** the problem, not building it. The build
happens in a **separate, new repository**, driven by a coding agent that reads this folder first.

## Why Problem 2
Chosen over audio search (P1) and novelty scoring (P3) because it is the only problem that uses
both of Garmit's rarest credentials at once: his **LLM-as-judge evaluation harness** at Amazon
and his **vision-foundation-model work** (Grounding-DINO, SAM) at MathWorks. It also hits three
of the G2 JD's "stand out" items: AI-generated content for end users, multimodal AI, and evals.
The full comparison was given in chat on 2026-09-25 and is not repeated here.

## Reading order

| File | For | Contents |
|---|---|---|
| [`01-problem-statement.md`](01-problem-statement.md) | Everyone | Organizers' text, Garmit's added constraints, the problem restated for an agent, 12 assumptions with defaults |
| [`02-scope-and-design.md`](02-scope-and-design.md) | Implementing agent | Typed inputs, market registry, pipeline, generation strategy, the three metrics, golden dataset, tests, success criteria, build order, repo layout, risks |
| [`03-models-apis-and-budget.md`](03-models-apis-and-budget.md) | Garmit, then agent | Verified model facts, SDK snippets, **what his subscriptions do and don't cover**, what to buy, budget, local models, morning checklist |
| [`04-prior-art.md`](04-prior-art.md) | Both | Existing systems, papers and eval methods, with what to take from each, and how this design differs from a typical submission |
| [`05-personal-context.md`](05-personal-context.md) | Implementing agent | Who Garmit is, what to showcase, how Gavel principles map here, honesty rules, how to work with him |
| [`AGENT_BRIEF.md`](AGENT_BRIEF.md) | New repo | Drop-in `AGENTS.md`/`CLAUDE.md`: mission, non-negotiables, architecture, build order, definition of done |

## Five things to know before reading further
1. **The free Gemini key cannot generate images.** Both allowed image models list "Free Tier:
   Not available". Enable billing before the event. About $0.067 per 1K image on Flash; the whole
   project fits in ~$15–25.
2. **"1K" is not "≤1024 px" except for square images.** At 1K, 16:9 comes out 1376×768. Default
   to 1:1 (1024×1024) and guard every output with a resize and a test.
3. **Claude Pro and ChatGPT Plus pay for the coding agents (Claude Code, Codex), not API
   calls.** A cross-family judge needs separate Anthropic (or OpenAI, or OpenRouter) credits.
4. **Google's own docs say text renders best when you generate the text first**, then ask for
   the image containing it. The pipeline plans text before the image call.
5. **The core experiment is the enrichment ablation.** Measure context adherence with the
   enriched brief vs the raw fields. It answers the problem's own premise with a number.

## Using this folder in the new repo
1. Create the new repo.
2. Copy `AGENT_BRIEF.md` to the repo root as `AGENTS.md` (and `CLAUDE.md`).
3. Copy `01`–`05` into `docs/context/`. They double as the "architectural requirements supplied
   to the agent" the organizers' disclosure asks for.
4. Start the agent with: *"Read AGENTS.md and docs/context/, then do milestone M0."*

## Open items for Garmit
- Put the 12 assumptions in `01` §4 to the organizers at the start of the event, if possible
- Buy/enable: Gemini billing (must), Anthropic credits (should), OpenRouter (optional). See `03` §4
- Photograph 4–5 products tonight, at least two with printed label text
