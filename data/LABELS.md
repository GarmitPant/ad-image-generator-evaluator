# Human labels

`labels.csv` is the human-labelled subset used by `adgen report` to check whether automated judgments are credible.

- **run_id**: a full run ID or a unique prefix (8 characters is enough).
- **candidate_index**: 1–4.
- **dimension**: `overall`, `text_selection`, `text_rendering`, `product` or `context`.
- **label**: `pass` or `fail`.
- **labeler / note**: who labelled it and why (free text).

Label from the images and inputs **before** reading the evaluator's results. One row per candidate × dimension. The report treats `fail` as the positive (defect) class and lists automated `unknown` verdicts as abstentions.
