# b1-12-heineken-ae-summer-exact · candidate 1

![candidate](../images/b1-12-heineken-ae-summer-exact__f45717d8-c1.png)

**Verdict: PASS** · score 1.0 · **winner** (approved)

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
| Same shape and silhouette | PASS | It has the same capped, long-necked glass-bottle silhouette. |
| Same colours and materials | PASS | The bottle is green glass with a green-and-white label and red stars. |
| Distinctive parts preserved | PASS | Red stars appear on the neck and oval front label, alongside vertical neck branding. |
| Product branding matches the reference | PASS | The bottle label visibly reads Heineken Original and Pure Malt Lager, matching the reference branding. |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.9307 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | Bright sunshine and green palms are consistent with a UAE summer; no contradictory seasonal cues appear. |
| No out-of-season elements | PASS | No snow, snowfall, frost, or blizzard is visible. |
| Setting plausible for the country | PASS | The architecture and palms are plausible for the UAE. |
| Country recognisable from the scene (diagnostic) | PASS (info) | The wind tower, lattice screen, pale stone architecture, and date palms evoke a traditional UAE setting. |
| No cultural caricature or costume shorthand | PASS | There are no people or caricatures; the regional cues are architecture and plants. |
| No flags; landmarks only in the background | PASS | No flags or national emblems are visible, and no landmark dominates the bottle. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | The sunny, palm-lined scene has no visible cue contradicting summer. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | Only one bottle is shown, with no people, vehicle, or depiction of drinking. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Heineken Original
Cold. Crisp. Refreshing.` | `Heineken Original Cold. Crisp. Refreshing.` | exact (whitespace-equivalent) | 0.0 |
