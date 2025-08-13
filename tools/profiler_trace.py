from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate profiling report from trace data")
    parser.add_argument("trace", nargs="?", default="profiler_trace.jsonl", help="JSON lines trace file")
    parser.add_argument("--out", default="profiler_report.json", dest="out")
    args = parser.parse_args()

    frames: list[float] = []
    subsystems: defaultdict[str, float] = defaultdict(float)
    trace_path = Path(args.trace)
    if trace_path.exists():
        with trace_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                dt = float(data.get("dt") or data.get("frame_time") or 0)
                frames.append(dt)
                for name, value in data.get("subsystems", {}).items():
                    subsystems[name] += float(value)
    avg_fps = len(frames) / sum(frames) if frames else 0.0
    if len(frames) >= 2:
        p95 = statistics.quantiles(frames, n=100)[94]
    elif frames:
        p95 = frames[0]
    else:
        p95 = 0.0
    total_sub = sum(subsystems.values())
    fractions = {name: (value / total_sub if total_sub else 0.0) for name, value in subsystems.items()}
    report = {
        "avg_fps": avg_fps,
        "p95_frame_ms": p95 * 1000,
        "subsystem_fraction": fractions,
    }
    with Path(args.out).open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
