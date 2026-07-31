import json
from dataclasses import asdict
from pathlib import Path

from harness.grading import GradeResult
from harness.runner import RunResult


def append_checkpoint(path: Path, result: RunResult) -> None:
    with path.open("a") as f:
        f.write(json.dumps(asdict(result)) + "\n")


def load_checkpoint(path: Path) -> list[RunResult]:
    if not path.is_file():
        return []

    results = []
    for line in path.read_text().splitlines():
        data = json.loads(line)
        grade_data = data["grade"]
        grade_data["refused_config"] = tuple(grade_data["refused_config"])
        results.append(
            RunResult(
                diff=data["diff"],
                grade=GradeResult(**grade_data),
                pi_stdout=data["pi_stdout"],
                pi_stderr=data["pi_stderr"],
            )
        )
    return results
