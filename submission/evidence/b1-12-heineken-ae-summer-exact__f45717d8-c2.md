# b1-12-heineken-ae-summer-exact · candidate 2

![candidate](../images/b1-12-heineken-ae-summer-exact__f45717d8-c2.png)

**Verdict: PASS** · score 1.0 · not selected

AE / summer · exact mode · plan guardrails: approved · evaluation ok

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
| Same type of product | PASS | The final image shows a Heineken beer bottle like the references. |
| Same shape and silhouette | PASS | It has the same capped, long-neck glass-bottle silhouette. |
| Same colours and materials | PASS | The bottle is green glass with a green, white, and red label. |
| Distinctive parts preserved | PASS | Red stars appear on the neck and front label, with vertical neck branding and a large oval front label. |
| Product branding matches the reference | PASS | The bottle label visibly reads Heineken, HEINEKEN ORIGINAL, and PURE MALT LAGER, matching the reference branding. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.9263 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | The sunny outdoor terrace and green palms are consistent with summer; no contradictory seasonal cue is visible. |
| No out-of-season elements | PASS | No snow, frost, or snowfall is visible. |
| Setting plausible for the country | PASS | The palm-lined terrace and patterned building are plausible in the UAE. |
| Country recognisable from the scene (diagnostic) | FAIL (info) | Palm trees and a patterned facade suggest a Gulf setting, but nothing visibly identifies the UAE specifically. |
| No cultural caricature or costume shorthand | PASS | No people or costumes are depicted; the regional cues are architecture and plants. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible, and no landmark dominates the product. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The sunny scene contains no visible cue contradicting UAE summer. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | A beer bottle is displayed alone; no drinking, driving, minors, or health claims are depicted. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Heineken Original
Cold. Crisp. Refreshing.` | `Heineken Original Cold. Crisp. Refreshing.` | exact (whitespace-equivalent) | 0.0 |
