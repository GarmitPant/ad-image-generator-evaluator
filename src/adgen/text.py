from .contracts import CopySelection, TextBlock, TextInput, word_count


def source_contract(spec: TextInput):
    source = spec.source_text
    spans = {(p.start, p.end) for p in spec.protected_spans}
    for phrase in spec.protected_phrases:
        if not phrase:
            raise ValueError("protected phrase cannot be empty")
        start = 0
        found = False
        while (start := source.find(phrase, start)) >= 0:
            spans.add((start, start + len(phrase)))
            found = True
            start += 1
        if not found:
            raise ValueError("protected phrase absent from source")
    if any(end > len(source) for _, end in spans):
        raise ValueError("protected span outside source")
    return {
        "version": "source/1",
        "mode": spec.mode,
        "source_text": source,
        "protected_spans": [{"start": a, "end": b} for a, b in sorted(spans)],
        "offset_unit": "unicode_codepoint",
        "capacity": {"blocks": 4, "visible_chars": 120, "words": 20},
    }


def exact_selection(contract):
    source = contract["source_text"]
    return CopySelection(
        blocks=[TextBlock(start=0, end=len(source), text=source, role="supporting_text")]
    )


def freeze_selection(contract, selection: CopySelection):
    source = contract["source_text"]
    selected = selection.blocks
    cursor = 0
    omissions = []
    blocks = []
    for index, block in enumerate(selected, 1):
        if block.start < cursor or block.end > len(source):
            raise ValueError("spans must be ordered, nonoverlapping and inside source")
        if source[block.start : block.end] != block.text or not block.text.strip():
            raise ValueError("selection must match exact visible source substring")
        if block.start > cursor:
            omissions.append(
                {"start": cursor, "end": block.start, "text": source[cursor : block.start]}
            )
        cursor = block.end
        blocks.append(
            {
                "block_id": f"t{index}",
                **block.model_dump(),
                "visible_chars": sum(not c.isspace() for c in block.text),
                "word_count": word_count(block.text),
                "linebreaks": block.text.count("\n"),
            }
        )
    if cursor < len(source):
        omissions.append({"start": cursor, "end": len(source), "text": source[cursor:]})
    for span in contract["protected_spans"]:
        # Every protected phrase remains contiguous in one displayed block.
        if not any(b.start <= span["start"] and b.end >= span["end"] for b in selected):
            raise ValueError("protected span omitted or split")
    if contract["mode"] == "exact" and (len(selected) != 1 or selected[0].text != source):
        raise ValueError("Exact must preserve all source content")
    if sum(b["visible_chars"] for b in blocks) > 120 or sum(b["word_count"] for b in blocks) > 20:
        raise ValueError(
            "copy exceeds pilot capacity (120 visible characters / 20 words); shorten the input"
        )
    return {
        "version": "text-plan/1",
        "mode": contract["mode"],
        "blocks": blocks,
        "omissions": omissions,
        "semantics_evaluated": False,
    }


def text_shape(plan):
    return [
        {
            key: block[key]
            for key in ("block_id", "role", "visible_chars", "word_count", "linebreaks")
        }
        for block in plan["blocks"]
    ]
