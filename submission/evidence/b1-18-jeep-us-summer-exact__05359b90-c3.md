# b1-18-jeep-us-summer-exact · candidate 3

![candidate](../images/b1-18-jeep-us-summer-exact__05359b90-c3.png)

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
| Same type of product | PASS | The final image shows a Jeep-style two-door off-road SUV. |
| Same shape and silhouette | PASS | Its boxy body, upright front, flared arches, and lifted stance match the reference silhouette. |
| Same colours and materials | PASS | Both vehicles have a dark body, dark trim, and large black tires. |
| Distinctive parts preserved | UNSURE | no answer/abstained |
| Product branding matches the reference | PASS | The Jeep name is legible above the grille. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.8878 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Bright sun, palms, and a clear beachside setting are consistent with summer. |
| No out-of-season elements | PASS | The scene is sunny, with clear pavement and no snow or frost. |
| Setting plausible for the country | PASS | The beachside streetscape is plausible for coastal Florida; nothing visible contradicts a US setting. |
| Country recognisable from the scene (diagnostic) | PASS (info) | Pastel Art Deco buildings, palms, a beach, and a colorful lifeguard tower evoke Miami Beach, Florida. |
| No cultural caricature or costume shorthand | PASS | No people or caricatures are depicted. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible; the background does not dominate the Jeep. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The sunny beachside scene has no visible cue contradicting summer. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | No alcohol or drinking is visible. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Summer is calling.
Answer it off-road.` | `Summer is calling. Answer it off-road.` | exact (whitespace-equivalent) | 0.0 |
