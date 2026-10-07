from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RQ3_ROOT = ROOT.parent
W3_ROOT = RQ3_ROOT.parent
EXP1_ROOT = Path(os.environ.get("EXP1_ROOT", W3_ROOT / "Exp1_User_Context_Embedding"))
W3_BACKUP_ROOT = Path(os.environ.get("W3_BACKUP_ROOT", "/scratch3/che489/W3-Backup/W3-repo"))

if str(EXP1_ROOT) not in sys.path:
    sys.path.insert(0, str(EXP1_ROOT))

import exp1_pipeline as e1


DEFENSES = {
    "StruQ": {"type": "prevention", "legacy_column": "struq_verdict"},
    "SecAlign": {"type": "prevention", "legacy_column": "secalign_verdict"},
    "DataSentinel-D": {"type": "detection", "legacy_column": "datasentinel_verdict"},
    "CausalArmor": {"type": "detection", "legacy_column": "causal_armor_verdict"},
}


def setup_dirs() -> None:
    for rel in [
        "00_config",
        "01_matched_manifest/rendered_prompts",
        "02_runs",
        "03_legacy_import",
        "04_processed",
        "05_statistics",
        "06_figures",
        "07_tables",
        "08_analysis",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def include_benign_controls() -> bool:
    return os.environ.get("RQ3_DEFENSE_INCLUDE_BM", "1").strip().lower() not in {"0", "false", "no", "n"}


def matched_conditions() -> list[tuple[str, str]]:
    conditions = [("E", "M"), ("UC", "M")]
    if include_benign_controls():
        conditions.extend([("E", "BM"), ("UC", "BM")])
    return conditions


def prompt_for(source: str, artifact_type: str, row: dict[str, Any], lookup: dict[str, Any]) -> str:
    desire = lookup["desires"][row["desire_id"]]
    prompt = desire["extended_user_prompt"]
    if source == "UC":
        offers = e1.candidate_offers(row, lookup)
        condition = "UC_M" if artifact_type == "M" else "UC_B"
        embedded = e1.embedded_context_text_for(condition, row, lookup, offers)
        if embedded:
            prompt = f"{prompt.rstrip()}\n{embedded}"
    return prompt


def build_matched_manifest() -> None:
    setup_dirs()
    lookup = e1.load_lookup()
    manifest = e1.load_manifest()
    rows = []
    for exp1_row in manifest:
        for defense, meta in DEFENSES.items():
            for source, artifact_type in matched_conditions():
                condition = f"{source}_{artifact_type}_{defense}"
                run_id = f"RQ3B_{exp1_row['pair_id']}_{condition}".replace("/", "_")
                prompt = prompt_for(source, artifact_type, exp1_row, lookup)
                artifact_id = exp1_row["malicious_artifact_id"] if artifact_type == "M" else exp1_row["benign_matched_id"]
                row = {
                    "rq": "RQ3",
                    "experiment": "DefenseCoverage",
                    "run_id": run_id,
                    "pair_id": exp1_row["pair_id"],
                    "base_task_id": exp1_row["base_task_id"],
                    "source": source,
                    "artifact_type": artifact_type,
                    "artifact_id": artifact_id,
                    "defense": defense,
                    "defense_type": meta["type"],
                    "condition": condition,
                    "model": os.environ.get("AGENTDOJO_OPENAI_MODEL", "gpt-4o-2024-05-13"),
                    "seed": exp1_row["seed"],
                    "candidate_order": exp1_row["candidate_order"],
                    "run_prompt": prompt,
                    "status": "manifest_only_runner_required",
                }
                rows.append(row)
                (ROOT / "01_matched_manifest/rendered_prompts" / f"{run_id}.txt").write_text(prompt + "\n", encoding="utf-8")
    write_json(ROOT / "00_config/00_defenses.json", DEFENSES)
    write_jsonl(ROOT / "01_matched_manifest/01_matched_defense_manifest.jsonl", rows)
    queue = [{"queue_index": idx, "run_id": row["run_id"], "defense": row["defense"], "source": row["source"], "artifact_type": row["artifact_type"]} for idx, row in enumerate(rows, 1)]
    write_jsonl(ROOT / "01_matched_manifest/02_run_queue.jsonl", queue)
    print(f"matched_defense_runs={len(rows)} benign_controls={include_benign_controls()}")


def iter_legacy_rows() -> list[dict[str, Any]]:
    pred_dir = W3_BACKUP_ROOT / "Detection-Methods" / "prediction result"
    files = [
        "agentdojo_travel_1540_combined.jsonl",
        "agentdojo_travel_1540_context_ignoring.jsonl",
        "agentdojo_travel_1540_escape_characters.jsonl",
        "agentdojo_travel_1540_fake_completion.jsonl",
        "agentdojo_travel_1540_naive.jsonl",
        "our-attack-full-set.jsonl",
    ]
    out = []
    for filename in files:
        path = pred_dir / filename
        if not path.exists():
            continue
        for row in read_jsonl(path):
            for defense, meta in DEFENSES.items():
                verdict = row.get(meta["legacy_column"], "")
                if not verdict:
                    continue
                out.append(
                    {
                        "dataset": filename,
                        "row_id": row.get("row_id"),
                        "defense": defense,
                        "defense_type": meta["type"],
                        "defense_triggered": verdict in {"BLOCKED", "ALLOWED"},
                        "defense_score": "",
                        "defense_blocked": verdict == "BLOCKED",
                        "verdict": verdict,
                        "legacy_design": "I/U+I/I+U_or_attack_dataset_not_matched_source",
                        "source": "legacy_uncontrolled",
                        "artifact_type": "unknown",
                    }
                )
    return out


def import_legacy() -> None:
    setup_dirs()
    rows = iter_legacy_rows()
    write_csv(ROOT / "03_legacy_import/01_legacy_defense_run_level.csv", rows)
    summary = []
    counts = Counter((row["dataset"], row["defense"], row["defense_type"], row["verdict"]) for row in rows)
    totals = Counter((row["dataset"], row["defense"], row["defense_type"]) for row in rows)
    for (dataset, defense, defense_type), total in sorted(totals.items()):
        blocked = counts[(dataset, defense, defense_type, "BLOCKED")]
        allowed = counts[(dataset, defense, defense_type, "ALLOWED")]
        summary.append(
            {
                "dataset": dataset,
                "defense": defense,
                "defense_type": defense_type,
                "n": total,
                "blocked": blocked,
                "allowed": allowed,
                "blocked_rate": blocked / total if total else "",
                "allowed_rate": allowed / total if total else "",
                "use": "appendix_legacy_only",
            }
        )
    write_csv(ROOT / "03_legacy_import/02_legacy_defense_summary.csv", summary)
    print(f"legacy_rows={len(rows)} legacy_summary_rows={len(summary)}")


def process_matched_results() -> None:
    setup_dirs()
    rows = []
    for path in sorted((ROOT / "02_runs").glob("**/15_trace_summary.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(payload)
    write_csv(ROOT / "04_processed/11_rq3b_run_level.csv", rows)
    print(f"matched_completed_rows={len(rows)}")


def statistics() -> None:
    setup_dirs()
    if not (ROOT / "03_legacy_import/02_legacy_defense_summary.csv").exists():
        import_legacy()
    process_matched_results()
    matched = read_csv(ROOT / "04_processed/11_rq3b_run_level.csv")
    summary = []
    if matched:
        grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
        for row in matched:
            grouped[(row.get("defense", ""), row.get("source", ""), row.get("artifact_type", ""))].append(row)
        for (defense, source, artifact_type), subset in sorted(grouped.items()):
            asr = sum(str(row.get("artifact_action_executed", "")).lower() in {"1", "true", "yes"} for row in subset) / len(subset)
            summary.append({"defense": defense, "source": source, "artifact_type": artifact_type, "n": len(subset), "adoption_or_asr": asr})
    write_csv(ROOT / "05_statistics/12_rq3b_defense_summary.csv", summary)
    gaps = []
    by_def_art: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in summary:
        by_def_art[(row["defense"], row["artifact_type"])][row["source"]] = row
    for (defense, artifact_type), sources in sorted(by_def_art.items()):
        if "E" in sources and "UC" in sources:
            gaps.append(
                {
                    "defense": defense,
                    "artifact_type": artifact_type,
                    "asr_e": sources["E"]["adoption_or_asr"],
                    "asr_uc": sources["UC"]["adoption_or_asr"],
                    "delta_source_uc_minus_e": float(sources["UC"]["adoption_or_asr"]) - float(sources["E"]["adoption_or_asr"]),
                }
            )
    write_csv(ROOT / "05_statistics/13_rq3b_source_gap.csv", gaps)
    write_csv(ROOT / "05_statistics/14_rq3b_regression.csv", [{"status": "pending_matched_rerun", "model": "AttackSuccess ~ Source x Defense"}])
    write_csv(ROOT / "07_tables/42_table_defense_coverage.csv", gaps if gaps else read_csv(ROOT / "03_legacy_import/02_legacy_defense_summary.csv"))
    analysis_md(summary, gaps)
    print(f"rq3b_summary_rows={len(summary)} gaps={len(gaps)}")


def analysis_md(summary: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> None:
    lines = [
        "# RQ3-B Existing Defense Coverage\n\n",
        "## Status\n\n",
        "- Matched primary rerun manifest is generated under `01_matched_manifest/`.\n",
        "- Legacy W3-Backup detector verdicts are imported under `03_legacy_import/`.\n",
        "- Legacy rows are appendix evidence only because source, position, and ordering are not isolated.\n\n",
        "## Matched Conditions\n\n",
        "- E_M + defense\n- UC_M + defense\n",
    ]
    if include_benign_controls():
        lines.append("- E_BM + defense\n- UC_BM + defense\n")
    lines.extend(["\n## Defenses\n\n", "- StruQ\n- SecAlign\n- DataSentinel-D\n- CausalArmor\n\n"])
    if gaps:
        lines.extend(["## Source Gaps\n\n", "| Defense | Artifact | E | UC | Delta |\n", "| --- | --- | ---: | ---: | ---: |\n"])
        for row in gaps:
            lines.append(f"| {row['defense']} | {row['artifact_type']} | {row['asr_e']} | {row['asr_uc']} | {row['delta_source_uc_minus_e']} |\n")
    else:
        lines.append("## Source Gaps\n\nPending matched rerun outputs.\n")
    (ROOT / "08_analysis/02_RQ3B_defense_coverage_analysis.md").write_text("".join(lines), encoding="utf-8")


def figures() -> None:
    setup_dirs()
    import matplotlib.pyplot as plt

    legacy = read_csv(ROOT / "03_legacy_import/02_legacy_defense_summary.csv")
    rows = [row for row in legacy if row.get("dataset") == "agentdojo_travel_1540_combined.jsonl"]
    if rows:
        labels = [row["defense"] for row in rows]
        values = [float(row["blocked_rate"]) for row in rows]
        plt.figure(figsize=(6, 3.5))
        plt.bar(range(len(values)), values)
        plt.xticks(range(len(values)), labels, rotation=20, ha="right")
        plt.ylim(0, 1)
        plt.ylabel("Legacy blocked rate")
        plt.tight_layout()
        plt.savefig(ROOT / "06_figures/33_fig_defense_source_gap.pdf")
        plt.close()
    write_json(ROOT / "06_figures/README.json", {"note": "Figure uses legacy blocked rates until matched E/UC rerun outputs exist."})


def main() -> None:
    setup_dirs()
    build_matched_manifest()
    import_legacy()
    statistics()
    figures()


if __name__ == "__main__":
    main()
