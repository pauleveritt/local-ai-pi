import shutil

import pytest

from harness.runner import RunResult, run_agentclinic_phase1


def _pi_and_server_available() -> bool:
    if shutil.which("pi") is None:
        return False
    try:
        from harness.liveness import check_model_server_alive

        check_model_server_alive()
    except Exception:
        return False
    return True


@pytest.mark.skipif(
    not _pi_and_server_available(),
    reason="requires pi on PATH and a live model server",
)
def test_run_agentclinic_phase1_returns_a_graded_result():
    result = run_agentclinic_phase1()

    assert isinstance(result, RunResult)
    assert result.grade.tests_expected == 4
