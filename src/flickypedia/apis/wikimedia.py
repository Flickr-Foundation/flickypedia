import httpx


def get_userinfo(access_token: str) -> str:
    """
    Returns the user ID and user info for a Wikimedia Commons user.
    """
    client = httpx.Client(headers={"Authorization": f"Bearer {access_token}"})

    resp = client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={"action": "query", "meta": "userinfo", "format": "json"},
    )

    return resp.json()["query"]["userinfo"]
