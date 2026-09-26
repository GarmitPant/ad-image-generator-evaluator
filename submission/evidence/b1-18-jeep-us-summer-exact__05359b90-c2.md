# b1-18-jeep-us-summer-exact · candidate 2

![candidate](../images/b1-18-jeep-us-summer-exact__05359b90-c2.png)

**Verdict: UNSURE** · score 0.9792 · not selected

US / summer · exact mode · plan guardrails: approved · evaluation ok

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

## Product (same object): UNSURE (score 0.9167)

| Check | Result | Why |
|---|---|---|
| Exactly one product visible | PASS | judge counted 1, detector counted 1; exactly one required and both must agree |
| Same type of product | PASS | The final image shows a two-door Jeep off-road vehicle like the reference. |
| Same shape and silhouette | PASS | It has the same boxy two-door silhouette, raised stance, and prominent wheel arches. |
| Same colours and materials | PASS | The dark body, dark hardtop, black trim, and knobby tires match the reference. |
| Distinctive parts preserved | UNSURE | no answer/abstained |
| Product branding matches the reference | PASS | The vehicle’s grille bears a legible “Jeep” label. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.8163 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | The trees are fully green, and no visible cue contradicts summer. |
| No out-of-season elements | PASS | The street and trees show no snow, frost, or snowfall. |
| Setting plausible for the country | PASS | The residential street, row houses, sidewalks, and hydrant are plausible in the United States. |
| Country recognisable from the scene (diagnostic) | PASS (info) | Brownstone-style row houses with stoops, fire escapes, and a street hydrant suggest a US city, particularly New York. |
| No cultural caricature or costume shorthand | PASS | No people or caricatures are visible; the architecture is background setting. |
| No flags; landmarks only in the background | PASS | No flags, national emblems, or dominant landmarks are visible. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | Green foliage and clear pavement do not contradict a summer setting. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | No alcohol or drinking is visible. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Summer is calling.
Answer it off-road.` | `Summer is calling. Answer it off-road.` | exact (whitespace-equivalent) | 0.0 |
