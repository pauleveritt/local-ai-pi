from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_home_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text
