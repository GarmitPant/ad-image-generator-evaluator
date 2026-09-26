# b1-04-bottle-de-winter-extract · candidate 1

![candidate](../images/b1-04-bottle-de-winter-extract__d897ef86-c1.png)

**Verdict: PASS** · score 1.0 · not selected

DE / winter · extract mode · plan guardrails: approved · evaluation ok

## Technical checks: PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Image file is readable | PASS | image decodes |
| Square and at most 1024 px | PASS | square and long edge <= 1024 |

## Text selection (input → copy): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Selected copy is an exact excerpt of the input | PASS | every block is an exact, ordered source span |
| Protected phrases kept whole | PASS | protected phrases kept whole |
| Copy fits the ad (max 4 blocks, 120 characters, 20 words) | PASS | within rendering capacity |
| Meaning preserved (no lost 'not', 'up to' or conditions) | PASS | judge answered yes |
| Nothing essential left out of the copy | PASS | judge answered no |
| Selected copy is relevant to the product or offer | PASS | judge answered yes |

## Text rendering (copy → image): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Every copy line appears once, spelled exactly | PASS | all 3 copy block(s) found exactly once |
| No duplicated or unplanned text | PASS | no unplanned ad text |
| Text is legible (confidence and size proxy) | PASS | legibility proxy: confident reads and text height >= min_text_height_px (never fails on its own) |

## Product (same object): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Exactly one product visible | PASS | judge counted 1, detector counted 1; exactly one required and both must agree |
| Same type of product | PASS | The final image shows the same type of reusable bottle. |
| Same shape and silhouette | PASS | Its cylindrical body, rounded shoulders, and flat cap match the reference silhouette. |
| Same colours and materials | PASS | The bottle has the same matte dark-green appearance. |
| Distinctive parts preserved | PASS | The green cap, narrow dark band beneath it, and faint seam near the bottle's base are visible. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.5683 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Snow along the canal and leafless trees are consistent with winter. |
| Setting plausible for the country | PASS | The brick warehouses, canal, cobblestones, and pretzel are plausible in Germany. |
| Country recognisable from the scene (diagnostic) | PASS (info) | A pretzel, cobblestones, and red-brick canal-side warehouses suggest a German setting. |
| No cultural caricature or costume shorthand | PASS | No people or costumes are visible; the scene uses architecture and food as setting cues. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible, and the buildings remain in the background. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | Snow and bare trees support the winter setting; no contradictory seasonal cues are visible. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | The image shows a reusable bottle, with no visible alcohol, drinking, minors, or driving. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Our insulated steel bottle keeps drinks hot for 12 hours and cold for 24 hours.` | `Our insulated steel bottle keeps drinks hot for 12 hours and cold for 24 hours.` | exact (whitespace-equivalent) | 0.0 |
| `Leak-proof lid.` | `Leak-proof lid.` | exact (whitespace-equivalent) | 0.0 |
| `Not dishwasher safe.` | `Not dishwasher safe.` | exact (whitespace-equivalent) | 0.0 |
