import httpx


def get_userinfo(access_token: str) -> str:
    """
    Returns the user ID and user info for a Wikimedia Commons user.
    """
    client = httpx.Client(headers={"Authorization": f"Bearer {access_token}"})

    resp = client.get(
        "https://commons.wikimedia.beta.wmflabs.org/w/api.php",
        params={"action": "query", "meta": "userinfo", "format": "json"},
    )
    from pprint import pprint; pprint(resp.json())
    resp.raise_for_status()

    return resp.json()["query"]["userinfo"]
