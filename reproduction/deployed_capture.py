import argparse
import json
from pathlib import Path

from source_relocation.spec import GUIDANCE


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def planned_cases(agents, tasks, rounds=3):
    cases = []
    for round_index in range(1, rounds + 1):
        for agent in agents:
            for task in tasks:
                for guidance in ("H1", "H2", "H3"):
                    cases.append({
                        "agent": agent["name"], "round": f"r{round_index}",
                        "task_id": task["task_id"], "guidance": guidance,
                        "prompt": (task["prompt"] + " " + GUIDANCE[guidance]).strip(),
                    })
    return cases


def collect(agents, tasks, output, rounds=3, headless=True):
    from playwright.sync_api import sync_playwright
    cases = planned_cases(agents, tasks, rounds)
    by_name = {agent["name"]: agent for agent in agents}
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    observed = {
        (row["agent"], row["round"], row["task_id"], row["guidance"])
        for row in read_jsonl(output)
    } if destination.is_file() else set()
    with sync_playwright() as playwright, destination.open("a", encoding="utf-8") as stream:
        browser = playwright.chromium.launch(headless=headless)
        try:
            for item in cases:
                key = item["agent"], item["round"], item["task_id"], item["guidance"]
                if key in observed:
                    continue
                config = by_name[item["agent"]]
                context_options = {}
                if config.get("storage_state"):
                    context_options["storage_state"] = config["storage_state"]
                context = browser.new_context(**context_options)
                page = context.new_page()
                status = "ok"
                answer = ""
                error = ""
                try:
                    page.goto(config["url"], wait_until="domcontentloaded",
                              timeout=int(config.get("timeout_ms", 60000)))
                    field = page.locator(config["input_selector"]).last
                    field.fill(item["prompt"])
                    responses = page.locator(config["response_selector"])
                    before = responses.count()
                    if config.get("submit_selector"):
                        page.locator(config["submit_selector"]).last.click()
                    else:
                        field.press("Enter")
                    page.wait_for_function(
                        """({selector, before}) => document.querySelectorAll(selector).length > before""",
                        arg={"selector": config["response_selector"], "before": before},
                        timeout=int(config.get("timeout_ms", 60000)),
                    )
                    answer = page.locator(config["response_selector"]).last.inner_text()
                except Exception as exc:
                    status = "error"
                    error = str(exc)
                finally:
                    context.close()
                record = {**item, "status": status, "output": answer, "error": error}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
        finally:
            browser.close()


def make_annotation_template(source, output):
    labels = ("E1", "E2", "E3", "C1", "C2", "C3")
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as stream:
        for observation in read_jsonl(source):
            record = dict(observation)
            for label in labels:
                record[label + "_applicable"] = None
                record[label + "_violation"] = None
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents", help="JSON file containing agent URLs and browser selectors")
    parser.add_argument("--tasks", help="JSONL with task_id and prompt")
    parser.add_argument("--out", default="outputs/deployed/observations.jsonl")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--annotation-template")
    parser.add_argument("--print-count", action="store_true")
    args = parser.parse_args()
    if args.annotation_template:
        make_annotation_template(args.out, args.annotation_template)
        return
    if not args.agents or not args.tasks:
        parser.error("--agents and --tasks are required for browser collection")
    agents = json.loads(Path(args.agents).read_text(encoding="utf-8"))
    tasks = read_jsonl(args.tasks)
    if args.print_count:
        print(len(planned_cases(agents, tasks, args.rounds)))
    else:
        collect(agents, tasks, args.out, args.rounds, not args.headed)


if __name__ == "__main__":
    main()
