# b1-07-jeep-gb-winter-exact · candidate 2

![candidate](../images/b1-07-jeep-gb-winter-exact__ab84c189-c2.png)

**Verdict: PASS** · score 1.0 · not selected

GB / winter · exact mode · plan guardrails: approved · evaluation ok

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
| Exact mode: the whole input is the copy | PASS | Exact mode keeps the entire input |
| Exact mode: nothing to select | PASS | Exact mode: the whole input is the copy; no selection to judge |

## Text rendering (copy → image): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Every copy line appears once, spelled exactly | PASS | all 1 copy block(s) found exactly once |
| No duplicated or unplanned text | PASS | no unplanned ad text |
| Text is legible (confidence and size proxy) | PASS | legibility proxy: confident reads and text height >= min_text_height_px (never fails on its own) |

## Product (same object): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Exactly one product visible | PASS | judge counted 1, detector counted 1; exactly one required and both must agree |
| Same type of product | PASS | The vehicle is a four-door Jeep Wrangler-style off-road SUV. |
| Same shape and silhouette | PASS | Its boxy four-door body, upright windshield and high-clearance stance match the reference. |
| Same colours and materials | PASS | It has the reference vehicle’s black body, dark flares, metal bumper and off-road tires. |
| Distinctive parts preserved | PASS | The seven-slot grille, round headlights, four doors, exposed hinges, large tires and side rails are visible; the rear spare-tire profile is not shown. |
| Product branding matches the reference | PASS | “Jeep” is legible above the grille, and “BFGoodrich” is legible on the front tire. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.9 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Frost on the ground and bare trees are consistent with a UK winter. |
| Setting plausible for the country | PASS | The stone village road and roadside postbox are plausible in the UK. |
| Country recognisable from the scene (diagnostic) | PASS (info) | A red pillar postbox, stone cottages and dry-stone walls are recognisable UK cues. |
| No cultural caricature or costume shorthand | PASS | No people or caricatures are visible; the regional cues are architecture and street furniture. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible, and no landmark dominates the product. |
| No religious imagery | PASS | No religious symbols, sites or ceremonies are visible. |
| No season contradictions | PASS | The frosty ground and bare trees do not contradict winter. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | No alcohol or drinking is visible. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Jeep Wrangler
Every road. Every weather.` | `Jeep Wrangler Every road. Every weather.` | exact (whitespace-equivalent) | 0.0 |
