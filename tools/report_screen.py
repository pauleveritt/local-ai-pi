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
  scope violations  paths outside both `writable` and the test roots
  wrote tests       tests the model added: permitted, never executed, and
                    a finding of its own rather than a failure
  overlap           share of the candidate found verbatim in the target's
                    own diff -- flagged above 90%, never acted on
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


    void = [r for r in records if r.get("validity", "valid") != "valid"]
    records = [r for r in records if r.get("validity", "valid") == "valid"]
    for record in void:
        print(f"VOID     {record['task_id']:26} {record['validity']}")
        for line in record.get("validity_evidence", [])[:3]:
            print(f"    {line}")
    if void:
        # Printed above the rates and excluded from all of them. A void
        # attempt is not a weak result; the grade describes a candidate
        # the model did not write.
        print()

    for record in records:
        violations = record["out_of_scope"]
        note = f"  scope:{list(violations)}" if violations else ""
        ov = record.get("reference_overlap", -1)
        # Printed, never acted on. A high score is a reason to read the
        # candidate; the copied `autowire` scored 100%, and so does a
        # six-line change the brief all but dictates.
        if ov >= 0.9:
            note += f"  OVERLAP:{ov:.0%}"
        if record.get("wrote_tests"):
            note += f"  +tests:{len(record['wrote_tests'])}"
        if record["model_timed_out"]:
            note += "  TIMED-OUT"
        # Printed on every line, never summarised away: a run that stopped
        # at the ceiling is not a run that could not do the work.
        if record.get("budget_exhausted", "none") != "none":
            note += f"  BUDGET:{record['budget_exhausted']}"
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
    tested = sum(1 for r in records if r.get("wrote_tests"))
    total = len(records)
    rules = sorted({r["rule_version"] for r in records})
    capped = sum(1 for r in records if r.get("budget_exhausted", "none") != "none")

    print(
        f"\ngap closed       {closed}/{total}"
        f"   (partial: {partial})"
        f"\naccepted         {accepted}/{total}"
        f"\nscope violations {scoped}/{total}"
        f"\nwrote tests      {tested}/{total}"
        f"\nbudget exhausted {capped}/{total}"
        f"\nrule version(s)  {rules}"
        + (f"\nVOID (excluded)  {len(void)}" if void else "")
    )
    if len(rules) > 1:
        print("MIXED RULE VERSIONS -- these records are not comparable")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
