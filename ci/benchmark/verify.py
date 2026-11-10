"""Reject missing measurements; this does not impose a production latency SLO."""

import json
import math
import sys
from pathlib import Path

EXPECTED = {"test_tool_catalog", "test_allowed_path"}


def verify_report(report):
    rows = report.get("benchmarks", [])
    names = [row.get("name") for row in rows]
    if len(rows) != len(EXPECTED) or set(names) != EXPECTED:
        raise ValueError("Both tool benchmarks must produce exactly one measurement")
    for row in rows:
        stats = row.get("stats", {})
        for key in ("min", "max", "mean", "rounds"):
            value = stats.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"Invalid benchmark statistic: {key}")
        if not stats["min"] <= stats["mean"] <= stats["max"]:
            raise ValueError("Inconsistent benchmark statistics")
    return {"measurements": len(rows), "names": sorted(names)}


if __name__ == "__main__":
    print(json.dumps(verify_report(json.loads(Path(sys.argv[1]).read_text()))))
