REGIONS = ("bos", "forced_decision", "generated_prefix", "target_artifact", "source_marker", "surrounding_context", "reliability_evidence", "external_content", "user_task", "other_trajectory", "other")


def span_indices(tokenizer, text: str, substrings: list[str]) -> set[int]:
    offsets = tokenizer(text, return_offsets_mapping=True).offset_mapping
    char_spans = []
    for sub in substrings:
        start = text.find(sub)
        while start >= 0:
            char_spans.append((start, start + len(sub)))
            start = text.find(sub, start + len(sub))
    return {i for i, (a, b) in enumerate(offsets) if b > a and any(a < right and b > left for left, right in char_spans)}


def assign_regions(tokenizer, text: str, artifact: str, user_task: str, source_label: str = "", reliability: str = "", decision_prefix: str = "Promo code:") -> list[str]:
    import json

    offsets = tokenizer(text, return_offsets_mapping=True).offset_mapping
    categories = ["other"] * len(offsets)
    if categories:
        categories[0] = "bos"

    def assign_span(left, right, category, allowed=None):
        for index, (start, end) in enumerate(offsets):
            if index == 0 or end <= start or start >= right or end <= left:
                continue
            if allowed is None or categories[index] in allowed:
                categories[index] = category

    serialized = text.rsplit("\n" + decision_prefix, 1)[0]
    try:
        messages = json.loads(serialized)
    except (ValueError, TypeError):
        messages = []
    if isinstance(messages, list):
        cursor = 0
        for message in messages:
            if not isinstance(message, dict):
                continue
            encoded = json.dumps(message, ensure_ascii=False)
            position = serialized.find(encoded, cursor)
            if position < 0:
                continue
            role = message.get("role")
            category = {
                "user": "surrounding_context",
                "tool": "external_content",
                "assistant": "other_trajectory",
                "system": "other_trajectory",
            }.get(role, "other_trajectory")
            assign_span(position, position + len(encoded), category)
            if role == "assistant" and artifact:
                sub = encoded.find(artifact)
                while sub >= 0:
                    assign_span(position + sub, position + sub + len(artifact), "generated_prefix")
                    sub = encoded.find(artifact, sub + len(artifact))
            cursor = position + len(encoded)

    if user_task:
        escaped = json.dumps(user_task, ensure_ascii=False)[1:-1]
        for label in (escaped, user_task):
            for i in span_indices(tokenizer, text, [label]):
                if i != 0 and categories[i] in ("surrounding_context", "other"):
                    categories[i] = "user_task"

    for index in span_indices(tokenizer, text, [source_label] if source_label else []):
        if index != 0:
            categories[index] = "source_marker"

    for marker in ('"role": "user"', '"role": "tool"', '"role": "assistant"', '"role": "system"'):
        for index in span_indices(tokenizer, text, [marker]):
            if index != 0:
                categories[index] = "source_marker"

    evidence_indices = span_indices(tokenizer, text, [reliability] if reliability else [])
    for index in evidence_indices:
        if index != 0:
            categories[index] = "reliability_evidence"

    decision_start = text.rfind("\n" + decision_prefix)
    if decision_start >= 0:
        assign_span(decision_start + 1, decision_start + 1 + len(decision_prefix), "forced_decision")

    artifact_indices = {
        index for index in span_indices(tokenizer, text, [artifact])
        if categories[index] not in (
            "reliability_evidence", "generated_prefix", "forced_decision", "source_marker"
        )
    }
    for index in artifact_indices:
        for neighbor in range(max(0, index - 12), min(len(categories), index + 13)):
            if categories[neighbor] in ("other", "external_content", "surrounding_context"):
                categories[neighbor] = "surrounding_context"
    for index in artifact_indices:
        categories[index] = "target_artifact"

    return categories


def attention_by_region(probe, text: str, regions: list[str], heads: list[tuple[int, int]], decision_position: int = -1) -> list[dict]:
    import torch
    inputs = probe.tokenizer(text, return_tensors="pt").to(probe.model.device)
    with torch.inference_mode():
        output = probe.model(**inputs, output_attentions=True, use_cache=False)
    result = []
    for layer, head in heads:
        values = output.attentions[layer][0, head, decision_position].float().cpu().numpy()
        for region in REGIONS:
            positions = [i for i, item in enumerate(regions) if item == region]
            mass = float(sum(values[i] for i in positions))
            result.append({"layer": layer, "head": head, "region": region, "tokens": len(positions), "mass": mass, "density": mass / len(positions) if positions else 0.0})
    return result


def artifact_attention_share(rows: list[dict]):
    grouped = {}
    for row in rows:
        key = row["layer"], row["head"]
        group = grouped.setdefault(key, {})
        group[row["region"]] = row["mass"]
    return [{"layer": layer, "head": head, "share": values.get("target_artifact", 0.0) / max(1e-12, values.get("target_artifact", 0.0) + values.get("surrounding_context", 0.0))} for (layer, head), values in grouped.items()]
