#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

This script is harness-agnostic. It can either:

- score pre-recorded trigger observations from a JSON file, or
- call an external adapter command that knows how to ask a specific harness
  whether the skill triggered for a given query.

Adapter contract:
- The adapter command receives a JSON request on stdin.
- It must write JSON to stdout.
- Supported responses are either `true` / `false` or an object with a
  boolean `triggered` field.
"""

import argparse
import json
import shlex
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def _parse_adapter_response(stdout: str) -> bool:
    """Parse an adapter response into a boolean trigger decision."""
    payload = json.loads(stdout.strip())
    if isinstance(payload, bool):
        return payload
    if isinstance(payload, dict) and "triggered" in payload:
        return bool(payload["triggered"])
    raise ValueError("Adapter output must be a JSON boolean or an object with a 'triggered' field")


def run_single_query(
    query: str,
    skill_name: str,
    skill_path: str,
    skill_description: str,
    timeout: int,
    adapter_command: str,
    model: str | None = None,
    run_index: int = 0,
) -> bool:
    """Run a single query through a harness-specific adapter."""
    request = {
        "query": query,
        "run_index": run_index,
        "skill": {
            "name": skill_name,
            "path": skill_path,
            "description": skill_description,
        },
    }
    formatted_command = adapter_command.format(
        model=model or "",
        skill_path=skill_path,
        skill_name=skill_name,
    )
    cmd = shlex.split(formatted_command)
    result = subprocess.run(
        cmd,
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Adapter exited {result.returncode}")
    return _parse_adapter_response(result.stdout)


def normalize_observations(observations: list[dict]) -> dict[str, list[bool]]:
    """Normalize observations into per-query trigger booleans."""
    query_triggers: dict[str, list[bool]] = {}
    for item in observations:
        query = item["query"]
        values = query_triggers.setdefault(query, [])
        if "triggered" in item:
            values.append(bool(item["triggered"]))
            continue

        if "triggers" in item and "runs" in item:
            true_runs = int(item["triggers"])
            total_runs = int(item["runs"])
            if total_runs < true_runs or total_runs < 1:
                raise ValueError(f"Invalid triggers/runs for query: {query}")
            values.extend([True] * true_runs)
            values.extend([False] * (total_runs - true_runs))
            continue

        raise ValueError(
            "Each observation must include either 'triggered' or both 'triggers' and 'runs'"
        )
    return query_triggers


def score_eval_set(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    query_triggers: dict[str, list[bool]],
    trigger_threshold: float,
) -> dict:
    """Score an eval set from per-query trigger observations."""
    results = []
    for item in eval_set:
        query = item["query"]
        triggers = query_triggers.get(query, [])
        if not triggers:
            raise ValueError(f"No trigger observations found for query: {query}")
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass = trigger_rate >= trigger_threshold if should_trigger else trigger_rate < trigger_threshold
        results.append(
            {
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for result in results if result["pass"])
    total = len(results)
    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    skill_path: Path,
    description: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    adapter_command: str | None = None,
    observations: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return scored results."""
    if observations is not None:
        query_triggers = normalize_observations(observations)
        return score_eval_set(eval_set, skill_name, description, query_triggers, trigger_threshold)

    if not adapter_command:
        raise ValueError("Provide either observations or an adapter command")

    query_triggers: dict[str, list[bool]] = {}
    query_items: dict[str, dict] = {}
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    str(skill_path),
                    description,
                    timeout,
                    adapter_command,
                    model,
                    run_idx,
                )
                future_to_info[future] = (item, run_idx)

        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_triggers.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as error:
                print(f"Warning: query failed: {error}", file=sys.stderr)
                query_triggers[query].append(False)

    return score_eval_set(eval_set, skill_name, description, query_triggers, trigger_threshold)


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument(
        "--adapter-command",
        default=None,
        help="Command used to query a specific harness. It receives a JSON request on stdin and must write JSON to stdout.",
    )
    parser.add_argument(
        "--observations",
        default=None,
        help="Optional path to a JSON file containing pre-recorded trigger observations",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model name forwarded to the adapter command via string formatting",
    )
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description
    observations = json.loads(Path(args.observations).read_text()) if args.observations else None

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        skill_path=skill_path,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        adapter_command=args.adapter_command,
        observations=observations,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for result in output["results"]:
            status = "PASS" if result["pass"] else "FAIL"
            rate_str = f"{result['triggers']}/{result['runs']}"
            print(f"  [{status}] rate={rate_str} expected={result['should_trigger']}: {result['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
