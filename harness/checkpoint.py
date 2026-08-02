import json
import os
from dataclasses import asdict
from pathlib import Path

from harness.grading import GradeResult
from harness.runner import RunConditions, RunResult


def append_checkpoint(path: Path, result: RunResult) -> None:
    record = (json.dumps(asdict(result)) + "\n").encode()
    with path.open("a+b") as checkpoint:
        checkpoint.seek(0)
        content = checkpoint.read()
        if content and not content.endswith(b"\n"):
            final_line_start = content.rfind(b"\n") + 1
            try:
                json.loads(content[final_line_start:])
            except json.JSONDecodeError:
                # Discard only the interrupted final fragment. Truncation
                # preserves earlier records; rewriting the file could lose
                # them if that rewrite itself were interrupted.
                checkpoint.truncate(final_line_start)
            else:
                checkpoint.seek(0, os.SEEK_END)
                checkpoint.write(b"\n")

        checkpoint.seek(0, os.SEEK_END)
        checkpoint.write(record)
        checkpoint.flush()
        os.fsync(checkpoint.fileno())


def load_checkpoint(path: Path) -> list[RunResult]:
    if not path.is_file():
        return []

    lines = path.read_text().splitlines()
    results = []
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                break
            raise
        grade_data = data["grade"]
        grade_data["refused_config"] = tuple(grade_data["refused_config"])
        results.append(
            RunResult(
                diff=data["diff"],
                grade=GradeResult(**grade_data),
                pi_stdout=data["pi_stdout"],
                pi_stderr=data["pi_stderr"],
                pi_returncode=data.get("pi_returncode"),
                pi_timed_out=data.get("pi_timed_out", False),
                conditions=(
                    RunConditions(
                        model=data["conditions"]["model"],
                        pi_command=tuple(data["conditions"]["pi_command"]),
                        pi_version=data["conditions"]["pi_version"],
                        task_spec_sha256=data["conditions"]["task_spec_sha256"],
                        harness_revision=data["conditions"]["harness_revision"],
                        run_timeout=data["conditions"]["run_timeout"],
                        grade_timeout=data["conditions"]["grade_timeout"],
                        extension_digests=tuple(
                            data["conditions"].get(
                                "extension_digests", ("<pre-cycle1>",)
                            )
                        ),
                    )
                    if data.get("conditions") is not None
                    else None
                ),
            )
        )
    return results
