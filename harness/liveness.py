import json
import urllib.request

TIMEOUT_SECONDS = 2


class ModelServerDown(Exception):
    """Raised when the model server does not respond at the expected endpoint."""


def check_model_server_alive(
    base_url: str = "http://127.0.0.1:8001",
    api_key: str = "not-needed",
) -> None:
    url = f"{base_url}/v1/models"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            json.loads(response.read())
    except Exception as exc:
        raise ModelServerDown(f"model server not reachable at {url}") from exc
