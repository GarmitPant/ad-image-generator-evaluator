# b1-20-heineken-br-winter-extract · candidate 3

![candidate](../images/b1-20-heineken-br-winter-extract__9d7cd589-c3.png)

**Verdict: PASS** · score 1.0 · not selected

BR / winter · extract mode · plan guardrails: approved · evaluation ok

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
| Same type of product | PASS | The product is a Heineken beer bottle. |
| Same shape and silhouette | PASS | Its long neck, rounded shoulders, and cylindrical body match the reference silhouette. |
| Same colours and materials | PASS | It has green glass, a green cap, and green-and-white labeling with red stars. |
| Distinctive parts preserved | PASS | Red stars appear on the neck and oval front label, with vertical Heineken neck branding. |
| Product branding matches the reference | PASS | The bottle label visibly reads “HEINEKEN ORIGINAL,” “Heineken,” and “PURE MALT LAGER.” |
| Visual similarity to the reference (diagnostic) | PASS (info) | DINOv2 cosine similarity to the closest reference: 0.9018 |

## Context (country, season, guardrails): PASS (score 1.0)

| Check | Result | Why |
|---|---|---|
| Scene fits the season | PASS | The sunny street scene has no visible cue that contradicts a Brazilian winter. |
| No out-of-season elements | PASS | No snow, snowfall, frost, or blizzard is visible. |
| Setting plausible for the country | PASS | The tiled facades, shutters, and palms are plausible in Brazil. |
| Country recognisable from the scene (diagnostic) | UNSURE (info) | no answer/abstained |
| No cultural caricature or costume shorthand | PASS | No people or costumes are shown; the scene uses architecture and plants. |
| No flags; landmarks only in the background | PASS | No flags, national emblems, or dominant landmarks are visible. |
| No religious imagery | PASS | No religious symbols, sites, or ceremonies are visible. |
| No season contradictions | PASS | Nothing visible contradicts a Brazilian winter setting. |
| No real people; no minors with age-restricted products | PASS | No people are visible. |
| Responsible depiction of alcohol | PASS | A beer bottle is shown without people, driving, drinking, or health claims. |

## Copy: expected vs read by OCR

| Expected | Read in image | Result | Character error rate |
|---|---|---|---|
| `Heineken Original.` | `Heineken Original.` | exact (whitespace-equivalent) | 0.0 |
| `Refreshing taste, pure malt.` | `Refreshing taste, pure malt.` | exact (whitespace-equivalent) | 0.0 |
| `Buy 2, get 1 free this week only.` | `Buy 2, get 1 free this week only.` | exact (whitespace-equivalent) | 0.0 |
| `Enjoy responsibly.` | `Enjoy responsibly.` | exact (whitespace-equivalent) | 0.0 |
