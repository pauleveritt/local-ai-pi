"""Report a screen directory's three rates, always together.

Reads saved attempt records; runs no model and no suite, so it can be
pointed at a run that is still in flight.

Three rates rather than one, because reporting acceptance alone has
already misled this project twice. A candidate that closes the whole
oracle gap and also writes a test grades `out-of-scope`, and an
acceptance-only headline reads that as failure. A candidate scoring 15/18
where the base already scores 15/18 has done nothing, and an
absolute-score headline reads that as a near-miss.

  gap closed        did the candidate move the oracle, and how far
  accepted          the full acceptance rule, scope violations included
  scope violations  paths written outside `writable`, a finding of its own
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", required=True, type=Path)
    args = parser.parse_args(argv)

    records = [
        json.loads(path.read_text())
        for path in sorted(args.dir.glob("*.json"))
        if path.name != "summary.json"
    ]
    if not records:
        print(f"no attempt records in {args.dir}")
        return 1

    for record in records:
        violations = record["out_of_scope"]
        note = f"  scope:{list(violations)}" if violations else ""
        if record["model_timed_out"]:
            note += "  TIMED-OUT"
        print(
            f"{record['task_id']:26} "
            f"{'FULL' if record['gap_closed'] >= 1.0 else '    '} "
            f"{'ACCEPT' if record['accepted'] else 'reject':7} "
            f"{record['outcome']:22} "
            f"delta {record['oracle_delta']:+3d}  "
            f"gap {record['gap_closed'] * 100:5.1f}%  "
            f"{record['model_seconds']:6.1f}s{note}"
        )

    closed = sum(1 for r in records if r["gap_closed"] >= 1.0)
    partial = sum(1 for r in records if 0 < r["gap_closed"] < 1.0)
    accepted = sum(1 for r in records if r["accepted"])
    scoped = sum(1 for r in records if r["out_of_scope"])
    total = len(records)
    rules = sorted({r["rule_version"] for r in records})

    print(
        f"\ngap closed       {closed}/{total}"
        f"   (partial: {partial})"
        f"\naccepted         {accepted}/{total}"
        f"\nscope violations {scoped}/{total}"
        f"\nrule version(s)  {rules}"
    )
    if len(rules) > 1:
        print("MIXED RULE VERSIONS -- these records are not comparable")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
