import json
import urllib.request

TIMEOUT_SECONDS = 2


class ModelServerDown(Exception):
    """Raised when the model server does not respond at the expected endpoint."""


def check_model_server_alive(
    base_url: str = "http://127.0.0.1:8001",
    api_key: str = "not-needed",
    timeout: float = TIMEOUT_SECONDS,
) -> None:
    """Confirm the model server responds, or raise ModelServerDown.

    All three parameters are seams with defaults matching BRIEF.md's
    recorded environment. `api_key` is sent as a Bearer token because
    oMLX requires the header to be present -- it does not check the
    value, but a missing header makes a healthy server answer 401 and
    read as down.
    """
    url = f"{base_url}/v1/models"
    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            json.loads(response.read())
    except Exception as exc:
        raise ModelServerDown(f"model server not reachable at {url}") from exc
