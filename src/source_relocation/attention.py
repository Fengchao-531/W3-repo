import torch

REGIONS = ("bos", "forced_decision", "generated_prefix", "target_artifact", "source_marker", "surrounding_context", "external_content", "user_task", "other_trajectory", "other")


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
    tokens = tokenizer(text, return_offsets_mapping=True).offset_mapping
    categories = ["other"] * len(tokens)
    if categories:
        categories[0] = "bos"
    mapping = [("user_task", [user_task]), ("surrounding_context", [reliability] if reliability else []), ("source_marker", [source_label] if source_label else []), ("forced_decision", [decision_prefix]), ("target_artifact", [artifact])]
    for category, substrings in mapping:
        for index in span_indices(tokenizer, text, [s for s in substrings if s]):
            categories[index] = category
    return categories


def attention_by_region(probe, text: str, regions: list[str], heads: list[tuple[int, int]], decision_position: int = -1) -> list[dict]:
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
