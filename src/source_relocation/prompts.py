import re
from .spec import BENEFITS, GUIDANCE, artifact_text


def render_request(task: str, description: str, position: str = "end", preference: str = "", instruction: str = "", guidance: str = "", reliability: str = "") -> str:
    task = task.strip()
    description = description.strip()
    if position == "beginning":
        pieces = [description, task]
    elif position == "middle":
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", task) if s.strip()]
        cut = max(1, len(sentences) // 2)
        pieces = [" ".join(sentences[:cut]), description, " ".join(sentences[cut:])]
    elif position == "end":
        pieces = [task, description]
    else:
        raise ValueError(position)
    if preference:
        if position == "end":
            pieces = [task, preference, description]
        else:
            pieces.insert(1, preference)
    return " ".join(p for p in [*pieces, instruction, reliability, guidance] if p).strip()


def experiment_conditions(rq: str, experiment: str):
    if rq == "rq1":
        if experiment == "relocation":
            return [("E", "M", "end", False, False, False, "H1"), ("UC_M", "M", "end", False, False, False, "H1"), ("UC_BM", "BM", "end", False, False, False, "H1")]
        if experiment == "position":
            return [(f"UC_{kind}_{position}", kind, position, False, False, False, "H1") for kind in ("M", "BM") for position in ("beginning", "middle", "end")]
        if experiment == "preference":
            return [(f"UC_{kind}_{suffix}", kind, "end", bool(pref), False, False, "H1") for kind in ("M", "BM") for suffix, pref in (("R_D", 0), ("R_P_D", 1))]
        if experiment == "instruction":
            return [("UC_P", "M", "end", True, False, False, "H1"), ("UC_P_I", "M", "end", True, True, False, "H1")]
        if experiment == "reliability":
            return [(f"{source}_{'V' if evidence else 'base'}", "M", "end", False, False, evidence, "H1") for source in ("E", "UC") for evidence in (False, True)]
        if experiment == "source_label":
            return [("C0", "M", "end", False, False, False, "H1"), ("C1", "M", "end", False, False, False, "H1"), ("C2", "BM", "end", False, False, False, "H1")]
    if rq == "rq3":
        if experiment == "verification":
            return [(f"{source}_{h}", "M", "end", False, False, False, h) for source in ("E", "UC") for h in GUIDANCE]
        if experiment == "defenses":
            return [(f"{source}_{kind}", kind, "end", False, False, False, "H1") for source in ("E", "UC") for kind in ("M", "BM")]
    raise ValueError((rq, experiment))


def render_condition(row: dict, condition: tuple, task: str) -> dict:
    name, kind, position, pref, instr, evidence, guidance = condition
    artifact = row["artifacts"][kind]
    external = name == "E" or name.startswith("E_")
    label_control = name in ("C0", "C1", "C2")
    desc = artifact_text(artifact, row["benefit"], row["carrier"])
    if label_control:
        lines = []
        for role in row["candidate_order"]:
            attributed = "user-provided" if (name == "C1" and role == "M") or (name == "C2" and role == "BM") else "external"
            lines.append(f"Source: {attributed}. " + artifact_text(row["artifacts"][role], row["benefit"], row["carrier"]))
        desc = " ".join(lines)
    info = BENEFITS[row["benefit"]]
    prompt = render_request(task, "" if external else desc, position, info["preference"] if pref else "", info["instruction"] if instr else "", GUIDANCE[guidance], info["evidence"] if evidence and not external else "")
    return {"condition": name, "source": "E" if external else "UC", "kind": kind, "prompt": prompt, "candidate_observation": info["evidence"] if evidence and external else "", "target_id": artifact.artifact_id, "guidance": guidance, "position": position}
