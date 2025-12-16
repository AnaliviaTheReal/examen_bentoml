import os
import time
import jwt
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")


def wait_for_api(timeout_s: int = 30) -> None:
    """Wait until the API is up (useful when docker just started)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/docs.json", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"API not ready after {timeout_s}s at {BASE_URL}")


def login(username="admin", password="admin123"):
    r = requests.post(
        f"{BASE_URL}/login",
        json={"payload": {"username": username, "password": password}},
        timeout=5,
    )
    return r


def predict(token: str | None, payload: dict):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"payload": payload},
        headers=headers,
        timeout=5,
    )
    return r


def test_login_success_returns_jwt():
    wait_for_api()
    r = login("admin", "admin123")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"
    assert isinstance(data.get("expires_in"), int)

    # Token looks like a JWT (3 parts)
    token = data["access_token"]
    assert token.count(".") == 2


def test_login_invalid_credentials_401():
    wait_for_api()
    r = login("admin", "wrongpassword")
    assert r.status_code == 401, r.text


def test_predict_missing_token_401():
    wait_for_api()
    payload = {
        "GRE Score": 320,
        "TOEFL Score": 110,
        "University Rating": 4,
        "SOP": 4.5,
        "LOR": 4.0,
        "CGPA": 9.2,
        "Research": 1,
    }
    r = predict(token=None, payload=payload)
    assert r.status_code == 401, r.text


def test_predict_invalid_token_401():
    wait_for_api()
    payload = {
        "GRE Score": 320,
        "TOEFL Score": 110,
        "University Rating": 4,
        "SOP": 4.5,
        "LOR": 4.0,
        "CGPA": 9.2,
        "Research": 1,
    }
    r = predict(token="this.is.not.valid", payload=payload)
    assert r.status_code == 401, r.text


def test_predict_success_returns_number():
    wait_for_api()
    r_login = login("admin", "admin123")
    assert r_login.status_code == 200, r_login.text
    token = r_login.json()["access_token"]

    payload = {
        "GRE Score": 320,
        "TOEFL Score": 110,
        "University Rating": 4,
        "SOP": 4.5,
        "LOR": 4.0,
        "CGPA": 9.2,
        "Research": 1,
    }
    r = predict(token=token, payload=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "predictions" in data
    assert isinstance(data["predictions"], list)
    assert len(data["predictions"]) == 1
    assert isinstance(data["predictions"][0], (int, float))


def test_predict_invalid_payload_422():
    wait_for_api()
    r_login = login("admin", "admin123")
    assert r_login.status_code == 200, r_login.text
    token = r_login.json()["access_token"]

    # Missing required fields / wrong types -> should be validation error
    bad_payload = {"GRE Score": "not_a_number"}
    r = predict(token=token, payload=bad_payload)
    assert r.status_code in (400, 422), r.text
