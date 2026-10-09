from dataclasses import dataclass
import torch


@dataclass
class TraceResult:
    scores: list[float]
    target_tokens: list[int]
    start: int


class InternalProbe:
    def __init__(self, model_id: str):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto", device_map="auto", attn_implementation="eager").eval()

    def input_ids(self, prefix: str, target: str):
        prefix_ids = self.tokenizer(prefix, add_special_tokens=True, return_tensors="pt").input_ids
        target_ids = self.tokenizer(target, add_special_tokens=False, return_tensors="pt").input_ids
        return torch.cat([prefix_ids, target_ids], dim=1).to(self.model.device), prefix_ids.shape[1], target_ids.squeeze(0).tolist()

    def layer_scores(self, context: str, artifact_code: str, decision_prefix: str = "Promo code:") -> TraceResult:
        text = context.rstrip() + "\n" + decision_prefix
        ids, start, target_ids = self.input_ids(text, artifact_code)
        with torch.inference_mode():
            outputs = self.model(ids, output_hidden_states=True, use_cache=False)
        decoder = self.model.get_decoder() if hasattr(self.model, "get_decoder") else self.model.model
        norm = decoder.norm if hasattr(decoder, "norm") else self.model.model.norm
        lm_head = self.model.get_output_embeddings()
        target = ids[:, start:]
        scores = []
        for states in outputs.hidden_states[1:]:
            logits = lm_head(norm(states[:, start - 1:-1, :])).float()
            logprobs = torch.log_softmax(logits, dim=-1)
            score = logprobs.gather(-1, target.unsqueeze(-1)).mean()
            scores.append(float(score.item()))
        return TraceResult(scores=scores, target_tokens=target_ids, start=start)

    def terminal_score(self, ids, start: int):
        with torch.inference_mode():
            outputs = self.model(ids, use_cache=False)
            logprobs = torch.log_softmax(outputs.logits[:, start - 1:-1].float(), dim=-1)
            return float(logprobs.gather(-1, ids[:, start:].unsqueeze(-1)).mean().item())

    def layer(self, index: int):
        decoder = self.model.get_decoder() if hasattr(self.model, "get_decoder") else self.model.model
        return decoder.layers[index]

    def patch(self, context_from: str, context_to: str, code: str, component: str, layer: int, head: int | None = None, prefix: str = "Promo code:"):
        input_from, start_from, _ = self.input_ids(context_from.rstrip() + "\n" + prefix, code)
        input_to, start_to, _ = self.input_ids(context_to.rstrip() + "\n" + prefix, code)
        index_from = torch.arange(start_from - 1, input_from.shape[1] - 1, device=self.model.device)
        index_to = torch.arange(start_to - 1, input_to.shape[1] - 1, device=self.model.device)
        assert len(index_from) == len(index_to)
        layer_obj = self.layer(layer)
        block = layer_obj.self_attn if component == "attention" else layer_obj.mlp
        cache = {}
        if head is not None:
            assert component == "attention"
            block = block.o_proj

        def record(module, inputs, output):
            cache["output"] = inputs[0].detach().clone() if head is not None else (output[0] if isinstance(output, tuple) else output).detach().clone()

        listener = block.register_forward_hook(record)
        with torch.inference_mode():
            self.model(input_from, use_cache=False)
        listener.remove()
        donor = cache["output"][:, index_from]

        if head is not None:
            def swap_inputs(module, inputs):
                data = inputs[0].clone()
                n_heads = self.model.config.num_attention_heads
                head_size = data.shape[-1] // n_heads
                sl = slice(head * head_size, (head + 1) * head_size)
                data[:, index_to.to(data.device), sl] = donor[:, :, sl].to(data.device)
                return (data, *inputs[1:])
            handle = block.register_forward_pre_hook(swap_inputs)
        else:
            def swap_output(module, inputs, output):
                data = output[0] if isinstance(output, tuple) else output
                patched = data.clone()
                patched[:, index_to.to(data.device), :] = donor.to(data.device)
                return (patched, *output[1:]) if isinstance(output, tuple) else patched
            handle = block.register_forward_hook(swap_output)
        try:
            baseline = self.terminal_score(input_to, start_to)
        finally:
            handle.remove()
        return {"base": self.terminal_score(input_to, start_to), "patched": baseline, "effect": baseline - self.terminal_score(input_to, start_to)}


def late_layer_summary(scores: list[float], threshold: float = 0.875) -> float:
    n = len(scores)
    return float(sum(score for index, score in enumerate(scores, 1) if index / n >= threshold) / sum(index / n >= threshold for index in range(1, n + 1)))


def matched_gap(probe: InternalProbe, external: str, user_context: str, code: str) -> dict:
    e = probe.layer_scores(external, code)
    uc = probe.layer_scores(user_context, code)
    diff = [u - x for u, x in zip(uc.scores, e.scores)]
    return {"code": code, "E": e.scores, "UC": uc.scores, "gap": diff, "late_mean": late_layer_summary(diff)}


def bidirectional_patch(probe: InternalProbe, external: str, user_context: str, code: str, component: str, layer: int, head: int | None = None) -> dict:
    e_to_uc = probe.patch(external, user_context, code, component, layer, head)
    uc_to_e = probe.patch(user_context, external, code, component, layer, head)
    return {"component": component, "layer": layer, "head": head, "E_to_UC": e_to_uc["effect"], "UC_to_E": uc_to_e["effect"], "bidirectional_mean": (e_to_uc["effect"] - uc_to_e["effect"]) / 2}


def head_set_effect(probe: InternalProbe, donor_context: str, recipient_context: str, code: str, heads: list[tuple[int, int]], prefix: str = "Promo code:") -> dict:
    donor_ids, donor_start, _ = probe.input_ids(donor_context.rstrip() + "\n" + prefix, code)
    receiver_ids, receiver_start, _ = probe.input_ids(recipient_context.rstrip() + "\n" + prefix, code)
    count = donor_ids.shape[1] - donor_start
    if receiver_ids.shape[1] - receiver_start != count:
        raise ValueError("Matched artifact tokenization differs between input conditions")
    cache = {}
    handles = []
    layers = sorted({layer for layer, _ in heads})
    for layer in layers:
        module = probe.layer(layer).self_attn.o_proj

        def make_cache(index):
            def record(mod, inputs):
                cache[index] = inputs[0][:, donor_start - 1:donor_start + count - 1].detach().clone()
            return record

        handles.append(module.register_forward_pre_hook(make_cache(layer)))
    try:
        with torch.inference_mode():
            probe.model(donor_ids, use_cache=False)
    finally:
        for handle in handles:
            handle.remove()
    baseline = probe.terminal_score(receiver_ids, receiver_start)
    updated = []
    for layer in layers:
        chosen = [head for selected_layer, head in heads if selected_layer == layer]
        module = probe.layer(layer).self_attn.o_proj

        def make_swap(index, selected):
            def replace(mod, inputs):
                data = inputs[0].clone()
                donor = cache[index].to(data.device)
                heads_count = probe.model.config.num_attention_heads
                width = data.shape[-1] // heads_count
                for head in selected:
                    window = slice(head * width, (head + 1) * width)
                    data[:, receiver_start - 1:receiver_start + count - 1, window] = donor[:, :, window]
                return (data, *inputs[1:])
            return replace

        updated.append(module.register_forward_pre_hook(make_swap(layer, chosen)))
    try:
        altered = probe.terminal_score(receiver_ids, receiver_start)
    finally:
        for handle in updated:
            handle.remove()
    return {"baseline": baseline, "patched": altered, "effect": altered - baseline, "heads": heads}


def selected_heads(rows: list[dict], count: int = 3):
    ranked = sorted(rows, key=lambda row: row["mean_effect"], reverse=True)
    positive = [row for row in ranked if row["mean_effect"] > 0][:count]
    counteracting = min(rows, key=lambda row: row["mean_effect"])
    return {"top": [(row["layer"], row["head"]) for row in positive], "counteracting": (counteracting["layer"], counteracting["head"])}


def evaluate_head_sets(probe: InternalProbe, contexts: list[dict], head_sets: dict[str, list[tuple[int, int]]]):
    results = []
    for row in contexts:
        for label, head_list in head_sets.items():
            e_to_uc = head_set_effect(probe, row["E"], row["UC"], row["code"], head_list)
            uc_to_e = head_set_effect(probe, row["UC"], row["E"], row["code"], head_list)
            results.append({"unit_id": row["unit_id"], "set": label, "E_to_UC": e_to_uc["effect"], "UC_to_E": uc_to_e["effect"], "bidirectional_mean": (e_to_uc["effect"] - uc_to_e["effect"]) / 2})
    return results
