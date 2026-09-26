# Live run: Ray-Ban sunglasses, AU summer, Extract

First real (non-synthetic) generation run, 2026-09-26. Curated from gitignored `runs/` as evaluator input data. Run ID `0d425b20667c4ae180bc26a10a93b550`, code at commit `fe6f52b`, run by Garmit with his own keys.

| Input | Value |
|---|---|
| Reference | [`../../products/sunglasses.jpg`](../../products/README.md) (single reference) |
| Geography / season | AU / summer (southern hemisphere, Dec–Feb) |
| Text mode | Extract; protected phrase "Built for bright days." |
| Candidates | 2 |
| Models | `gpt-6-sol` (extract, analysis, plan, review) · `gemini-3.1-flash-image` (images) |

## Files

| File | Content |
|---|---|
| `request.json` | The request, with the image path rewritten relative to this folder |
| `text-plan.json` | Frozen selection: 4 exact source spans plus omissions |
| `resolved-context.json`, `product-profile.json` | Shared evaluator inputs |
| `candidates/cN/image.png` | Published 1024×1024 image, byte-identical to the export |
| `candidates/cN/creative-plan.json`, `guardrail-review.json`, `prompt.txt` | Per-candidate plan, review and exact image prompt |
| `calls.json` | 8 model calls: models, usage, timestamps and **report-only** cost estimates (~$0.19 total). Dashboards are authoritative |
| `summary.json` | Pipeline export summary (`generated_unscored`, no winner) |
| Human labels | Go in the shared [`data/labels.csv`](../../labels.csv), keyed by run ID and candidate index |

## Agent observations (not human labels, not evaluator output)

Recorded by Claude Code while inspecting the run. Human labels in `data/labels.csv` should be made independently.

- **Selection:** "classic black frames" · "Polarized lenses." · "Built for bright days." · "Free returns within 30 days on all orders placed online." All are exact spans, and the protected phrase is intact (19 words, limit 20). "classic black frames" was given role `product_name`, which is debatable. Its lowercase comes from the source and is correct under exact rendering.
- **c1:** all four blocks appear once, exactly and legibly. The frame shape and colour match. The lens logo is close to "Ray-Ban P"; the temple script is slightly malformed. Coastal summer scene; no stereotypes observed.
- **c2:** **"Built for bright days." is rendered twice** (right-middle and lower-right). The prompt contains the string once (`prompt.txt`), so this is a generation-side rendering failure, not a compiler bug. It is a naturally occurring negative for the rendering check (duplicate or unexpected text). Product and scene are otherwise similar to c1.
- **Planner detail:** c2's `product_placement.orientation` ends mid-word ("curved arms leg") at exactly the schema's 100-character limit, so the model truncated its own output. Harmless here.

## Limitations

Two images from one request is anecdotal. They are fixtures, not results. The Ray-Ban trademark appears because the reference shows it; see the product provenance notes.
