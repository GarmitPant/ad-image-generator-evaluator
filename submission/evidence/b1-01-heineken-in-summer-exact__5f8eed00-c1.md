# b1-01-heineken-in-summer-exact · candidate 1

![candidate](../images/b1-01-heineken-in-summer-exact__5f8eed00-c1.png)

**Verdict: PASS** · score 1.0 · **winner** (approved)

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
| Same type of product | PASS | The product is a Heineken beer bottle. |
| Same shape and silhouette | PASS | It has the reference bottle's narrow neck, rounded shoulders, and straight-sided body. |
| Same colours and materials | PASS | The green glass, green cap, and green-and-white label match the references. |
| Distinctive parts preserved | PASS | Red stars appear on the neck and front label, with vertical Heineken neck branding and a large oval front label. |
| Product branding matches the reference | PASS | The bottle label visibly reads Heineken, HEINEKEN ORIGINAL, and PREMIUM MALT LAGER; smaller print is less clear. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.892 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Rain and wet streets are consistent with India's June–August monsoon; nothing visibly contradicts the season. |
| No out-of-season elements | PASS | The street is wet with rain; no snow, snowfall, frost, or blizzard is visible. |
| Setting plausible for the country | PASS | The rainy urban street, taxi, and roadside barriers are plausible for India. |
| Country recognisable from the scene (diagnostic) | PASS (info) | A black-and-yellow taxi and matching roadside barriers are recognisable cues of an Indian city, particularly Mumbai. |
| No cultural caricature or costume shorthand | PASS | No people or costumes are depicted; the regional cues are street details. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible, and the background building does not dominate the bottle. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The rainy scene has no visible cue contradicting a June–August monsoon setting. |
| No real people; no minors with age-restricted products | PASS | No identifiable people are visible. |
| Responsible depiction of alcohol | PASS | No people are shown drinking or driving, and no minors or health claims are visible. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Heineken Original
Made for monsoon evenings.
Enjoy responsibly.` | `Heineken Original Made for monsoon evenings. Enjoy responsibly.` | exact (whitespace-equivalent) | 0.0 |
