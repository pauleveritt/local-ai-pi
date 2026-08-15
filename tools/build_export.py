"""Derive the curated collaborator export from the import graph.

The first export (2026-08-11) was built from a hand-curated keep-list.
Two reviews and one test run found five files it got wrong: kept tests
importing cut modules, a kept `tests/fixtures/README.md` documenting four
fixtures it had not carried, and a kept `reference-patches` reader whose
data was cut. Hand-curating a 120-file closure is not something to do
twice.

So this derives it instead. Python modules come from walking the real
import graph (via `ast`, including imports inside function bodies -- the
hand-built list missed `tools.audit_attempt` imported inside
`test_screen.py` test functions). Tests are kept only when every
first-party module they import is itself kept. Everything that is *data*
rather than code stays an explicit list below, because no import graph
can find it -- but those lists are small enough to read.

    uv run python -m tools.build_export --out /tmp/export-tree

This writes a tree. It does not touch git; committing the result to the
`collaborator-export` branch is a separate, deliberate step.
"""

import argparse
import ast
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The product path's entry points. Everything reachable from these by
# import is kept; nothing else is.
ENTRY_POINTS = (
    "tools/deliver_candidate.py",
    # tools/run_cycle7_confirmatory_batch.py is deliberately NOT here. It
    # reproduces one pre-registered batch that has already run and whose
    # result is committed; a collaborator does not need to re-run it to
    # use or understand the engine, and re-running it is a new experiment
    # rather than a check on this one. Dropping it also drops
    # harness/intervals.py and harness/model_config.py, which nothing
    # else imports -- 823 lines of reproduction machinery in total.
    #
    # It stays in the research repository, where the confirmatory result
    # cites it by name. The export's own copy of that result says where
    # to find it.
    # tools/qualify_workload.py is deliberately NOT here any more. It was,
    # for one bad reason: tests/test_workload.py imported it, so excluding
    # it dropped all 73 of that file's tests -- 70 of which cover
    # harness/workload.py, which *is* product path. A review named that
    # exactly: tests should not determine the product boundary. Splitting
    # harness/qualification.py and tests/test_qualification.py out
    # (2026-08-12) removed the coupling, so the export can now decline
    # qualification and keep full coverage of the module it does ship.
)

# Data the import graph cannot see. Kept deliberately short so it can be
# read and checked by eye.
DATA_PATHS = (
    "workloads/svcs/cohort.toml",
    "workloads/svcs/env/pyproject.toml",
    "workloads/svcs/env/uv.lock",
    "workloads/svcs/cells/gemma12b-implementer-v1.toml",
)
SUPPORTED_TASKS = (
    "flask-extensions",
    "stringified-annotations",
    "local-pings",
    "autowire",
)

# Pi extensions are loaded by path at runtime, never imported, so no
# graph walk finds them. This is implementer.ts's same-repo import
# closure plus probe-cap.ts (which `harness/cell_resolution.py` names for
# bare-envelope mode). Deliberately NOT carried: author-cap.ts,
# envelope-cap.ts, proposal-limit.ts -- those are named only by
# `harness/screen.py`, which the product path no longer imports.
EXTENSION_PATHS = (
    "extensions/orchestration/handoff-contract.ts",
    "extensions/orchestration/implementer-policy.ts",
    "extensions/orchestration/implementer.ts",
    "extensions/orchestration/mutation-engine.ts",
    "extensions/orchestration/tool-target.ts",
    "extensions/orchestration/orchestration.test.ts",
    "extensions/guards/types.ts",
    "extensions/guards/loop-breaker.ts",
    "extensions/guards/preserve-symbols.ts",
    "extensions/guards/guards.test.ts",
    "extensions/probe-cap.ts",
    ".pi/extensions/loop-breaker.ts",
)

# The guard replay harness. No import graph reaches it -- it is JavaScript,
# and its fixtures are named on argv by a shell command rather than by any
# module. It comes along because it is the cheapest evidence in the project
# to reproduce: no model, no server, no network, one command.
REPLAY_HARNESS = ("tools/replay_guards.mjs",)
REPLAY_FIXTURE_DIR = "tests/fixtures/guards"

DOC_PATHS = (
    "docs/what-is.md",
    "docs/quickstart.md",
    "docs/contributing.md",
    "docs/evidence-index.md",
    "docs/model-setup.md",
    "docs/engine/loop-breaker.md",
    "docs/engine/setup.md",
    "docs/glossary.md",
    "docs/sdd.md",
    "docs/engine/example-brief.md",
)

# Flattened into docs/evidence/ in the export, since docs/superpowers/
# (the full Phase 1-6 design record) does not come along.
EVIDENCE_DOCS = (
    "docs/superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md",
    "docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md",
    "docs/superpowers/research/2026-08-11-evidence-archive-index.md",
)

ROOT_FILES = (
    "LICENSE",
    ".gitignore",
    # uv.lock is NOT taken from the source repo -- export-overlay/ supplies
    # its own. The source lock resolves the source pyproject (fastapi,
    # turbohtml, sphinx); overlaying the lean pyproject on top of it left
    # `uv lock --check` dirty and made `uv sync --frozen` install the old
    # 48-package tree. Regenerate the overlay lock with `uv lock` inside a
    # built export whenever the overlay pyproject changes.
    "package.json",
    "bun.lockb",
    "conftest.py",
    "pi-agent-dir/README.md",
    "pi-agent-dir/models.json",
    "pi-agent-dir/settings.json",
)


EVIDENCE_README = """# Evidence

The documents in this directory are **reproduced verbatim** from the
research repository. They are the record of what was pre-registered and
what was found, and they are not edited to match this export.

That means they name things you will not find here:

- `tools/run_cycle7_confirmatory_batch.py` -- the driver that produced
  the confirmatory batch.
- `harness/intervals.py` -- the tested Wilson/Newcombe helper the result
  quotes its intervals from.
- `harness/model_config.py` -- the scoped `models.json` bump the batch
  ran under.

All three live in the research repository. They are reproduction
machinery: needed to run *that* batch again, not to use or understand
the engine this export ships. Re-running the driver produces a new,
separate batch -- it is not a check on the result recorded here, which
is why the export does not carry it.

The engine those documents evaluate *is* here, and
[`../architecture.md`](../architecture.md) traces it.
"""


def first_party_imports(path: Path) -> set[str]:
    """Every `harness.*` / `tools.*` module a file imports, at any depth.

    Walks the whole AST rather than just module-level statements: the
    hand-built keep-list missed `tools.audit_attempt`, imported inside
    `test_screen.py` function bodies, and shipped an export whose tests
    failed on it.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in {"harness", "tools"}:
                    found.add(alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.level == 0
            and node.module.split(".")[0] in {"harness", "tools"}
        ):
            found.add(node.module)
            # `from harness import runner` imports the *submodule*
            # harness.runner, and recording only "harness" loses it --
            # `harness/__init__.py` exists, `harness.py` does not, so
            # the dependency silently resolved to nothing. That shipped
            # four uncollectable tests into the first derived export.
            for alias in node.names:
                found.add(f"{node.module}.{alias.name}")
    return found


def module_to_path(module: str) -> Path | None:
    candidate = REPO / (module.replace(".", "/") + ".py")
    return candidate if candidate.is_file() else None


def closure(entry_points: Iterable[str]) -> set[str]:
    """Transitive first-party import closure, as repo-relative paths."""
    kept: set[str] = set()
    frontier = [REPO / e for e in entry_points]
    while frontier:
        current = frontier.pop()
        rel = str(current.relative_to(REPO))
        if rel in kept:
            continue
        kept.add(rel)
        for module in first_party_imports(current):
            target = module_to_path(module)
            if target and str(target.relative_to(REPO)) not in kept:
                frontier.append(target)
    # Package __init__ files for anything kept.
    for package in {Path(p).parent for p in kept}:
        init = REPO / package / "__init__.py"
        if init.is_file():
            kept.add(str(init.relative_to(REPO)))
    return kept


def path_literals(path: Path) -> set[str]:
    """Repo-relative paths a file names as string literals.

    Imports are not the only dependency a test has. `test_research_records.py`
    parametrizes over files in `docs/superpowers/research/`,
    `test_doc_quotes.py` scans `docs/superpowers/{chapters,research}`, and
    `test_extensions.py` asserts `examples/extensions/word-count.ts` exists.
    None of them import anything first-party, so an import-graph walk keeps
    all three -- and the first derived export shipped a suite that failed
    collection outright because those directories are not in it.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    roots = {
        "docs",
        "examples",
        "workloads",
        "improvements",
        "tests",
        "extensions",
        "harness",
        "tools",
        ".pi",
    }
    found: set[str] = set()

    def record(value: str) -> None:
        value = value.strip("/")
        if "/" in value and value.split("/")[0] in roots:
            found.add(value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            record(node.value)
        # `Path(...) / "docs" / "superpowers" / "research"` -- pathlib's
        # division operator, which is how both test_research_records.py
        # and test_extensions.py name their data. A plain constant scan
        # misses these entirely (no single literal contains a slash), and
        # missing them shipped an export whose suite would not collect.
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            parts: list[str] = []
            current: ast.expr = node
            while isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div):
                if isinstance(current.right, ast.Constant) and isinstance(
                    current.right.value, str
                ):
                    parts.append(current.right.value)
                else:
                    parts.append("*")
                current = current.left
            record("/".join(reversed(parts)))
    return found


def keepable_tests(
    code_closure: set[str], data_paths: set[str]
) -> tuple[set[str], dict[str, set[str]]]:
    """Tests whose imports AND referenced paths are all present in the export.

    Returns (kept, rejected -> what disqualified it) so rejections are
    printed rather than silently dropped.
    """
    available = code_closure | data_paths
    kept: set[str] = set()
    rejected: dict[str, set[str]] = {}
    for test in sorted((REPO / "tests").glob("test_*.py")):
        rel = str(test.relative_to(REPO))
        missing = {
            str(p.relative_to(REPO))
            for module in first_party_imports(test)
            if (p := module_to_path(module)) is not None
            and str(p.relative_to(REPO)) not in code_closure
        }
        # A referenced path disqualifies the test only when it exists in
        # the source but is being cut -- a literal naming something that
        # never existed is the test's own problem, not the export's.
        for literal in path_literals(test):
            source = REPO / literal
            if not source.exists():
                continue
            if literal in available:
                continue
            if any(
                a == literal or a.startswith(literal.rstrip("/") + "/")
                for a in available
            ):
                continue
            missing.add(literal)
        if missing:
            rejected[rel] = missing
        else:
            kept.add(rel)
    return kept, rejected


def _rewrite_links(out: Path) -> None:
    """Repoint links that the flattening invalidated.

    `docs/superpowers/` does not come along, and the three evidence
    documents that do are flattened into `docs/evidence/`. Every link to
    them -- and every link *between* them, written when they were three
    directories apart -- is wrong in the export. The first derived export
    shipped 14 such links.

    Anything pointing at material the export deliberately excludes is
    de-linked to inline code rather than repaired: the target genuinely
    is not here, and a link that resolves to nothing is worse than prose
    naming the file.
    """
    flattened = {Path(d).name for d in EVIDENCE_DOCS}
    for md in sorted(out.rglob("*.md")):
        text = original = md.read_text()
        for name in flattened:
            depth = (
                "../" * len(md.relative_to(out / "docs").parts[:-1])
                if md.is_relative_to(out / "docs")
                else ""
            )
            for stale in (
                f"superpowers/specs/{name}",
                f"superpowers/research/{name}",
                f"../specs/{name}",
                f"../research/{name}",
                f"../plans/{name}",
            ):
                text = text.replace(f"]({stale})", f"]({depth}evidence/{name})")
            # Siblings inside docs/evidence/ reference each other by bare name.
            if md.parent.name == "evidence":
                text = text.replace(f"]({depth}evidence/{name})", f"]({name})")
        # Documents excluded from the export by name -- same treatment as
        # the pattern below, but they sit as bare siblings inside
        # docs/evidence/ so no directory prefix identifies them.
        for excluded in (
            "2026-08-11-phase7-cleanup-and-distribution-brief.md",
            "2026-08-11-phase7-clean-machine-rehearsal.md",
            "2026-08-11-morning-summary.md",
        ):
            text = re.sub(
                r"\[`?([^\]`]+)`?\]\((?:\.\./)*" + re.escape(excluded) + r"\)",
                r"`\1`",
                text,
            )
        # Targets the export does not carry: keep the words, drop the link.
        text = re.sub(
            r"\[`?([^\]`]+)`?\]\((?:\.\./)*(?:superpowers|workloads|plans|research|specs)/[^)]*\)",
            r"`\1`",
            text,
        )
        if text != original:
            md.write_text(text)


def build(out: Path) -> None:
    code = closure(ENTRY_POINTS)

    data: set[str] = (
        set(DATA_PATHS)
        | set(EXTENSION_PATHS)
        | set(DOC_PATHS)
        | set(ROOT_FILES)
        | set(REPLAY_HARNESS)
        | {
            str(f.relative_to(REPO))
            for f in sorted((REPO / REPLAY_FIXTURE_DIR).glob("*.json"))
        }
    )
    for task in SUPPORTED_TASKS:
        for name in ("manifest.toml", "brief.md", "qualification.json"):
            data.add(f"workloads/svcs/tasks/{task}/{name}")
        data.add(f"workloads/svcs/contracts/locating/{task}.md")
    # Deliberately NOT a blanket copy of tests/fixtures/. The first
    # version carried all of it -- ~1,270 lines of old drafts and
    # telemetry -- for tests that were then rejected anyway, and shipped
    # tests/fixtures/README.md describing four files it had not carried.
    # Only fixtures a kept test actually names come along; the loop below
    # runs after `tests` is known, so it is applied there.

    # Fixtures are resolved against the *kept* tests, so this runs in two
    # passes: decide the tests without fixtures available, then add back
    # only what those tests name.
    tests, rejected = keepable_tests(code, data)
    # A fixture comes along when a kept test names its file name. Those are
    # distinctive enough to match on; bare *directory* names are not, and
    # matching on them was a real bug -- merging `main` added
    # `tests/fixtures/guards/`, the word "guards" appears in unrelated test
    # sources, and six JSON files shipped into the export with nothing in
    # it that read them.
    #
    # Matching on a directory *path* instead would be sound but is dead
    # code, so it is not here. `keepable_tests` above already rejects any
    # test naming a rooted path absent from `available`, and fixtures are
    # not in `available` during that pass -- so a kept test can only name a
    # `tests/fixtures/...` path that `data` already carries, and re-adding
    # it selects nothing. Verified: no test in the current export names one.
    #
    # Known limitation, no current instance: a test that reaches its
    # fixtures unrooted (`Path(__file__).parent / "fixtures" / x`) and then
    # globs them is kept, because `path_literals` only records paths under
    # a known top-level root. Its fixtures would be dropped and the glob
    # would find nothing -- a vacuous pass rather than a loud failure. If
    # that ever gets written, name the fixture files.
    sources = [(REPO / t).read_text() for t in sorted(tests)]
    fixtures = {
        str(f.relative_to(REPO))
        for f in sorted((REPO / "tests" / "fixtures").rglob("*"))
        if f.is_file() and any(f.name in source for source in sources)
    }
    paths: set[str] = set(code) | tests | data | fixtures

    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.split()
    )
    missing = sorted(p for p in paths if p not in tracked)
    if missing:
        sys.exit("refusing to build: not tracked in git:\n  " + "\n  ".join(missing))

    if out.exists():
        shutil.rmtree(out)
    for rel in sorted(paths):
        destination = out / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, destination)

    # The evidence documents move to a flatter home, since the full
    # docs/superpowers/ tree does not come along.
    (out / "docs" / "evidence").mkdir(parents=True, exist_ok=True)
    for rel in EVIDENCE_DOCS:
        shutil.copy2(REPO / rel, out / "docs" / "evidence" / Path(rel).name)
    # These are frozen records: they describe what actually produced a
    # result, including machinery the export does not carry. Editing them
    # to match the export would falsify the record, so the boundary is
    # explained beside them instead.
    (out / "docs" / "evidence" / "README.md").write_text(EVIDENCE_README)

    _rewrite_links(out)

    overlay = REPO / "export-overlay"
    applied = []
    if overlay.is_dir():
        # git ls-files, not rglob: an unrestricted walk copied an
        # untracked .ruff_cache/ into the export, because ruff runs over
        # this directory like any other. Only tracked overlay files ship.
        overlay_tracked = subprocess.run(
            ["git", "ls-files"], cwd=overlay, capture_output=True, text=True, check=True
        ).stdout.split()
        for rel_name in sorted(overlay_tracked):
            source = overlay / rel_name
            if not source.is_file():
                continue
            rel = Path(rel_name)
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, out / rel)
            applied.append(str(rel))

    print(f"code modules:   {len(code)}")
    print(f"tests kept:     {len(tests)}")
    print(f"tests rejected: {len(rejected)}")
    for name, blockers in sorted(rejected.items()):
        print(f"    {name}  <- {', '.join(sorted(blockers))}")
    print(f"overlay files:  {len(applied)}  {applied}")
    print(f"total files:    {sum(1 for p in out.rglob('*') if p.is_file())}")
    print(f"written to:     {out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="directory to write the export tree into",
    )
    args = parser.parse_args(argv)
    build(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
