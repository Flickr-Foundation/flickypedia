import httpx


class WikimediaApi:
    """
    This is a thin wrapper for calling the Wikimedia API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the error handling in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, access_token):
        self.client = httpx.Client(
            base_url="https://commons.wikimedia.org",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def _call(self, **params):
        resp = self.client.get(url="w/api.php", params={**params, "format": "json"})

        if "error" in resp.json():
            raise WikimediaApiException(resp)

        return resp.json()

    def get_userinfo(self) -> str:
        """
        Returns the user ID and name for a Wikimedia Commons user.

            >>> get_userinfo(access_token="…")
            {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._call(action="query", meta="userinfo")

        return resp["query"]["userinfo"]


class WikimediaApiException(Exception):
    def __init__(self, resp):
        error_info = resp.json()["error"]

        self.code = error_info.get("code")
        self.error_info = error_info
        super().__init__(error_info.get("info"))
