# b1-06-modelo-us-autumn-extract · candidate 1

![candidate](../images/b1-06-modelo-us-autumn-extract__b9ba8505-c1.png)

**Verdict: PASS** · score 1.0 · not selected

US / autumn · extract mode · plan guardrails: approved · evaluation ok

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
| Every copy line appears once, spelled exactly | PASS | all 4 copy block(s) found exactly once |
| No duplicated or unplanned text | PASS | no unplanned ad text |
| Text is legible (confidence and size proxy) | PASS | legibility proxy: confident reads and text height >= min_text_height_px (never fails on its own) |

## Product (same object): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Exactly one product visible | PASS | judge counted 1, detector counted 1; exactly one required and both must agree |
| Same type of product | PASS | The final image shows a Modelo Especial beer bottle. |
| Same shape and silhouette | PASS | The bottle has the same narrow neck, rounded shoulders and straight-sided body. |
| Same colours and materials | PASS | It retains the amber glass, gold-colored neck and cap, and white front label. |
| Distinctive parts preserved | PASS | Droplets, the neck's large M and lion motifs, Modelo label, crimped gold-colored cap and lower-label barcode are visible. |
| Product branding matches the reference | PASS | The bottle label shows Modelo, Especial and CERVEZA; EST. 1925 appears beneath the neck's M. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.8675 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Yellow fallen leaves cover parts of the sidewalk; no visible cue contradicts autumn. |
| Setting plausible for the country | PASS | The taxi, sidewalk and brownstone-style streetscape are plausible in the United States. |
| Country recognisable from the scene (diagnostic) | PASS (info) | A yellow city taxi, brownstone-style stoops and black iron railings suggest New York City. |
| No cultural caricature or costume shorthand | PASS | No people or caricatures are depicted. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible; the streetscape remains background context. |
| No religious imagery | PASS | No religious symbols, sites or ceremonies are visible. |
| No season contradictions | PASS | Fallen yellow leaves are consistent with autumn. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | The bottle sits on a table; no people, drinking, or connection between the alcohol and the background taxi is shown. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Modelo Especial` | `Modelo Especial` | exact (whitespace-equivalent) | 0.0 |
| `Up to 20% off 12-packs at selected stores this weekend only.` | `Up to 20% off 12-packs at selected stores this weekend only.` | exact (whitespace-equivalent) | 0.0 |
| `21+ to purchase.` | `21+ to purchase.` | exact (whitespace-equivalent) | 0.0 |
| `Please drink responsibly.` | `Please drink responsibly.` | exact (whitespace-equivalent) | 0.0 |
