"""Authenticates against the Gancio login endpoint (v1 or v2)."""

import requests


def get_token(base_url: str, username: str, password: str, gancio_version: int = 2) -> str:
    """
    Authenticate and return a Bearer access token.

    v1: POST /oauth/login  (form-encoded, fields: username/password/grant_type/client_id)
    v2: POST /api/login/token  (JSON, fields: email/password)
    """
    if gancio_version == 1:
        resp = requests.post(
            f"{base_url}/oauth/login",
            data={
                "username": username,
                "password": password,
                "grant_type": "password",
                "client_id": "self",
            },
            timeout=15,
        )
    else:
        resp = requests.post(
            f"{base_url}/api/login/token",
            json={
                "email": username,
                "password": password,
            },
            timeout=15,
        )

    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("Kein access_token in der Antwort")
    return token
