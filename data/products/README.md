# Reference product images

Originals supplied by Garmit on 2026-09-26 (jeep images added later that day), committed byte-for-byte (no resizing or re-encoding). Source URLs come from each file's macOS download metadata (`kMDItemWhereFroms`); all six are Unsplash downloads. Pipeline code must derive normalized renditions from these files rather than overwrite them.

| File | Product | Pixels | SHA-256 | Source (Unsplash photo / photographer slug) |
|---|---|---|---|---|
| `heineken-1.jpg` | Heineken bottle, green studio background | 4000×6000 | `9e4b4d30ba54a6106578e385e0849882e8e5964f9b4a9a55cd4fd6e3de4f012e` | `mhad_4H6S14` / soliman-cifuentes |
| `heineken-2.jpg` | Heineken bottle, dark background, wet surface | 2624×3936 | `aadc584f97472c5199719d953becec68b7bafdb5a57dfd96e674f83a18e1308f` | `eYZTepIHYVU` / forrest-givens |
| `heineken-3.jpg` | Heineken bottle, warm indoor scene | 5304×7952 | `4014390e64719f7843fc183b60cfad365e20605a3a8d344f17a88a7a49da15ad` | `RCCTK-Affrc` / mike-peng |
| `modelo.jpg` | Modelo Especial bottle | 2400×3000 | `290ad8deb7ae013654c0496964ae5456e384d07d73805e89156918560ebd618e` | `qkW55UbeWdI` / soliman-cifuentes |
| `sunglasses.jpg` | Black Ray-Ban style sunglasses | 6000×6000 | `3afbb533f3dfa67bf365303f10c1670257279915f533fb70159c036176fa0de6` | `K62u25Jk6vo` / giorgio-trovato |
| `water-bottle.jpg` | Unbranded matte green insulated bottle | 4006×6008 | `0d4c98326207445863b7d0b6ec1431cf935c9d8fc0907ba257bf760f443e2491` | `reEySFadyJQ` / joan-tran |
| `jeep-1.jpg` | Black Jeep Wrangler Unlimited (4-door), lifted, residential street | 6720×3780 | `3b6c9d2e4129c3de18b5764adfff3a313c2458b2f13aad71311b69cfd365c5e3` | `x3JjUy9txjI` / aj-festa |
| `jeep-2.jpg` | Black Jeep Wrangler **2-door**, snowy mountain road | 6000×4000 | `30a38cf4885e41ed7d13074dbb3ab8aa7c1be2cb423330a26379260135bba3cb` | `OfRq2n3mbJ8` / jacob-sangster |
| `jeep-3.jpg` | Black Jeep Wrangler Unlimited (4-door), desert at dusk | 4400×2663 | `d6b063630a5e97ff6f8d5f078b02882083e2cec78140d998eb492607d370a9ff` | `yDekvyZ52dU` / quilia |

Photo pages: `https://unsplash.com/photos/<photo id>`.

## Notes for evaluation design

- **Heineken ×3:** the same product in three settings. These are useful for checking identity across references and for allowed variation in viewpoint and lighting.
- **Modelo:** same category (beer bottle), different brand. It is the natural wrong-brand negative against Heineken.
- **Water bottle:** plain, no text on it. Identity rests on colour, silhouette and cap. Its green is close to Heineken green, which makes it a colour-only confuser.
- **Sunglasses:** a small, low-contrast logo on the lens and temple, so the label may be unreadable at 1K. Use a predeclared visibility rule rather than a required transcription.

- **Jeep:** jeep-1 and jeep-3 show the same 4-door model and can be combined as references. **jeep-2 is a 2-door variant, so never combine it with the others.** Its snowy background makes it a season-leakage probe in summer requests. Licence plates count as product text, not ad copy.

## Limitations

- The Unsplash licence covers the photographs, not the trademarks shown (Heineken, Modelo, Ray-Ban). Generated ads that use these brands are research demonstrations, not brand-authorized creative. State this in the write-up.
- `heineken-3.jpg` is about 42.2 MP. That exceeds the proposed 40 MP input limit in `docs/design/01-generation-pipeline.md` §3A, so that limit needs revisiting or the image needs an explicit pre-downscale step.
