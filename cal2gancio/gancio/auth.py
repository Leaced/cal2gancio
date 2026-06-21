"""Authenticates against the Gancio OAuth endpoint."""

import requests


def get_token(base_url: str, username: str, password: str) -> str:
    """
    POST to /oauth/login and return a Bearer access token.
    Raises on HTTP errors or missing token.
    """
    resp = requests.post(
        f"{base_url}/oauth/login",
        data={
            "username":   username,
            "password":   password,
            "client_id":  "self",
            "grant_type": "password",
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("Kein access_token in der Antwort")
    return token
