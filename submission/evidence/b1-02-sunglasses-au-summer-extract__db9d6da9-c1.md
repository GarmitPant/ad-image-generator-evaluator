# b1-02-sunglasses-au-summer-extract · candidate 1

![candidate](../images/b1-02-sunglasses-au-summer-extract__db9d6da9-c1.png)

**Verdict: PASS** · score 1.0 · not selected

AU / summer · extract mode · plan guardrails: approved · evaluation ok

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
| Same type of product | PASS | The final image shows sunglasses like the reference product. |
| Same shape and silhouette | PASS | The rectangular, slightly upswept frame and temples match the reference silhouette. |
| Same colours and materials | PASS | Both have glossy black frames and dark tinted lenses. |
| Distinctive parts preserved | PASS | Two tinted lenses, an integrated bridge, oval corner accents, and curved temple tips are visible. |
| Product branding matches the reference | PASS | “Ray-Ban P” is visible on the lens, and Ray-Ban branding appears on the temple. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.9697 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Bright light, an open-air coastal setting, and a pool are consistent with summer; no contradictory cue is visible. |
| No out-of-season elements | PASS | No snow, snowfall, frost, or blizzard is visible. |
| Setting plausible for the country | PASS | A sunny coastal terrace with a pool is plausible in Australia. |
| Country recognisable from the scene (diagnostic) | FAIL (info) | The coastal view, tree, and sandstone-coloured building do not uniquely identify Australia. |
| No cultural caricature or costume shorthand | PASS | No people or caricatures are shown. |
| No flags; landmarks only in the background | PASS | No flags, national emblems, or dominant landmarks are visible. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The sunny coastal scene has no visible cue contradicting summer. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | No alcohol, drinking, or driving is shown. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `classic black frames` | `classic black frames` | exact (whitespace-equivalent) | 0.0 |
| `Polarized lenses. Built for bright days.` | `Polarized lenses. Built for bright days.` | exact (whitespace-equivalent) | 0.0 |
| `Free returns within 30 days on all orders placed online.` | `Free returns within 30 days on all orders placed online.` | exact (whitespace-equivalent) | 0.0 |
