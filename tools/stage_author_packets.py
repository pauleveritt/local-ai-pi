"""Stage one author packet per task, outside the repository and the cache.

The packet is the author's entire world: the base tree and the brief. It
lives under `~/.satyrn-authoring/`, deliberately not under `.workloads/`,
whose immediate sibling is `svcs.git` -- every target commit and every
oracle. Staging an author's inputs next to the answer key and then asking
it not to look is not a firewall, it is a request.

That is layout hygiene, not confinement, and the design says so. The
teeth are elsewhere: the author runs with `--tools read` only, so it has
no shell to go looking with. Cycle 1 established what happens when a
model with a shell finds something it should not have -- and that the
only place the evidence survives is the transcript, so the authoring
transcripts are saved and audited like any other attempt.
"""

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.workload as workload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".workloads"))
    parser.add_argument("--root", type=Path, default=Path.home() / ".satyrn-authoring")
    args = parser.parse_args(argv)

    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    clone = workload.ensure_clone(cohort.upstream, args.cache)

    manifest_root = args.root.resolve()
    if manifest_root == Path.cwd() or manifest_root in Path.cwd().parents:
        raise SystemExit(f"refusing to stage packets at {manifest_root}: contains cwd")

    index = {}
    for task_id in cohort.included:
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        packet = args.root / task_id
        shutil.rmtree(packet, ignore_errors=True)
        workload.export_tree(clone, manifest.base_sha, packet / "repo")
        shutil.copy2(manifest.brief_path, packet / "brief.md")

        # A packet that accidentally contains an oracle file is a
        # contaminated contract and a wasted arm, so check rather than
        # trust the export.
        leaked = [
            name
            for name in manifest.oracle_files
            if (packet / "repo" / name).is_file()
            and workload.sha256_file(packet / "repo" / name)
            == manifest.oracle_files_sha256.get(name)
        ]
        if leaked:
            raise SystemExit(f"{task_id}: packet contains target oracle files {leaked}")

        index[task_id] = {
            "packet": str(packet),
            "base_sha": manifest.base_sha,
            "brief_sha256": workload.sha256_file(packet / "brief.md"),
            "files": sum(1 for _ in (packet / "repo").rglob("*") if _.is_file()),
        }
        print(f"{task_id:26} {index[task_id]['files']:5} files  {packet}")

    (args.root / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True))
    print(f"\n{len(index)} packets staged under {args.root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
