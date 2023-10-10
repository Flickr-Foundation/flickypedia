import httpx


class WikimediaApiException(Exception):
    def __init__(self, resp):
        error_info = resp.json()["error"]

        self.code = error_info.get("code")
        self.error_info = error_info
        super().__init__(error_info.get("info"))


def get_userinfo(access_token: str) -> str:
    """
    Returns the user ID and name for a Wikimedia Commons user.

        >>> get_userinfo(access_token="…")
        {"id": 829939, "name": "Alexwlchan"}

    See https://www.mediawiki.org/wiki/API:Userinfo
    """
    client = httpx.Client(headers={"Authorization": f"Bearer {access_token}"})

    resp = client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={"action": "query", "meta": "userinfo", "format": "json"},
    )

    if "error" in resp.json():
        raise WikimediaApiException(resp)

    return resp.json()["query"]["userinfo"]
