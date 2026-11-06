#!/usr/bin/env python3
"""Compare the cost of LoomFlow and KaizenFlow runs from Claude Code transcripts.

Usage: python3 scripts/flow-cost.py [--since YYYY-MM-DD]

Weighted tokens = input + 1.25 * cache write + 0.1 * cache read + 5 * output.
They are relative to input price and ignore the price of each model. Active
minutes are the gaps between events in a session, each capped at 15 minutes,
so a long user pause counts as 15 minutes.
"""
import argparse
import datetime as dt
import glob
import json
import os
import statistics

ROOT = os.path.expanduser("~/.claude/projects")
GAP_CAP_SECONDS = 900


def read_transcript(path):
    """Return usage per API message, event times, and the slash commands used."""
    usage, times, commands = {}, [], set()
    with open(path, errors="replace") as lines:
        for line in lines:
            for flow in ("kaizenflow", "loomflow"):
                if f"<command-name>/{flow}" in line:
                    commands.add(flow)
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("timestamp"):
                times.append(event["timestamp"])
            message = event.get("message")
            if event.get("type") == "assistant" and isinstance(message, dict) and message.get("usage"):
                usage[message.get("id") or event.get("uuid")] = message["usage"]
    return list(usage.values()), times, commands


def weighted(usage):
    return sum(
        u.get("input_tokens", 0)
        + 1.25 * u.get("cache_creation_input_tokens", 0)
        + 0.1 * u.get("cache_read_input_tokens", 0)
        + 5 * u.get("output_tokens", 0)
        for u in usage
    )


def active_minutes(times):
    points = sorted(dt.datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times)
    gaps = ((b - a).total_seconds() for a, b in zip(points, points[1:]))
    return sum(min(gap, GAP_CAP_SECONDS) for gap in gaps) / 60


def role_of(agent_path):
    try:
        with open(agent_path[: -len(".jsonl")] + ".meta.json") as meta:
            return json.load(meta).get("agentType", "")
    except (OSError, ValueError):
        return ""


def measure(session_path):
    """Return (flow, row) for one session, or None if it ran no flow."""
    main_usage, times, commands = read_transcript(session_path)
    usage = list(main_usage)
    folder = session_path[: -len(".jsonl")] + "/subagents"
    roles = set()
    for agent in glob.glob(folder + "/**/agent-*.jsonl", recursive=True):
        agent_usage, agent_times, _ = read_transcript(agent)
        usage += agent_usage
        times += agent_times
        roles.add(role_of(agent))
    if "kaizenflow" in commands or "kaizen-reviewer" in roles:
        flow = "kaizenflow"
    elif "loomflow" in commands or any(role.startswith("pr-") for role in roles):
        flow = "loomflow"
    else:
        return None
    if not times:
        return None
    return flow, {
        "start": min(times)[:10],
        "weighted": weighted(usage),
        "main_share": weighted(main_usage) / max(1, weighted(usage)),
        "minutes": active_minutes(times),
        "main_calls": len(main_usage),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", default="0000-00-00")
    since = parser.parse_args().since
    runs = {}
    for path in glob.glob(ROOT + "/*/*.jsonl"):
        result = measure(path)
        if result and result[1]["start"] >= since:
            runs.setdefault(result[0], []).append(result[1])
    print("flow        runs  weighted M  active min  main calls  main share  (medians)")
    for flow, rows in sorted(runs.items()):
        def median(key):
            return statistics.median(row[key] for row in rows)

        print(
            f"{flow:11} {len(rows):4}  {median('weighted') / 1e6:10.2f}  {median('minutes'):10.0f}"
            f"  {median('main_calls'):10.0f}  {median('main_share'):10.0%}"
        )


if __name__ == "__main__":
    main()
