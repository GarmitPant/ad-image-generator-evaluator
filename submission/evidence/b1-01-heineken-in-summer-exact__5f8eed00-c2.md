# b1-01-heineken-in-summer-exact · candidate 2

![candidate](../images/b1-01-heineken-in-summer-exact__5f8eed00-c2.png)

**Verdict: PASS** · score 1.0 · not selected

IN / summer · exact mode · plan guardrails: approved · evaluation ok

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
| Same type of product | PASS | The final image shows a Heineken beer bottle. |
| Same shape and silhouette | PASS | It has the reference bottle's narrow neck, rounded shoulders, and straight-sided body. |
| Same colours and materials | PASS | The bottle is green glass with a green cap and green, white, and red labeling. |
| Distinctive parts preserved | PASS | Red stars appear on the neck and front label, with vertical Heineken neck branding and a large oval front label. |
| Product branding matches the reference | PASS | The bottle label visibly reads Heineken, Heineken Original, and Pure Malt Lager, matching the reference branding. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.8636 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Lush green palms and warm-weather surroundings are consistent with India's June–August monsoon season. |
| No out-of-season elements | PASS | No snow, frost, or snowfall is visible. |
| Setting plausible for the country | PASS | The tiled roofs, palms, and veranda are plausible in India; nothing visibly contradicts the setting. |
| Country recognisable from the scene (diagnostic) | PASS (info) | Coconut palms, red laterite-style walls, clay-tiled roofs, and a shaded veranda evoke coastal Kerala, India. |
| No cultural caricature or costume shorthand | PASS | No people or costumes are depicted; regional cues come from architecture and plants. |
| No flags; landmarks only in the background | PASS | No flags, national emblems, or prominent landmarks are visible. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The lush tropical scene has no visible cue contradicting the June–August season. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | Only a beer bottle is shown; there are no people, vehicles, or drinking activity. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Heineken Original
Made for monsoon evenings.
Enjoy responsibly.` | `Heineken Original Made for monsoon evenings. Enjoy responsibly.` | exact (whitespace-equivalent) | 0.0 |
