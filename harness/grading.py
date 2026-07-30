from dataclasses import dataclass

from harness.grading_plugin import DONE_MARKER


@dataclass(frozen=True)
class GradeResult:
    accepted: bool
    tests_executed: int
    tests_expected: int
    returncode: int
    stdout: str
    stderr: str


def _verdict(
    results_text: str, tests_expected: int, returncode: int, stdout: str, stderr: str
) -> GradeResult:
    lines = results_text.splitlines()
    done = DONE_MARKER in lines

    outcomes: dict[str, str] = {}
    for line in lines:
        if "\t" not in line:
            continue
        nodeid, outcome = line.split("\t", 1)
        outcomes[nodeid] = outcome
    tests_executed = len(outcomes)

    accepted = (
        done
        and tests_executed == tests_expected
        and tests_expected > 0
        and all(outcome == "passed" for outcome in outcomes.values())
        and returncode == 0
    )

    return GradeResult(
        accepted=accepted,
        tests_executed=tests_executed,
        tests_expected=tests_expected,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
