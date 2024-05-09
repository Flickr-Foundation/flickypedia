"""
Methods for getting info about Wikimedia Commons users.
"""

import typing

from .base import WikimediaApiBase


class UserInfo(typing.TypedDict):
    id: str
    name: str


class UserMethods(WikimediaApiBase):
    def get_userinfo(self) -> UserInfo:
        """
        Returns the user ID and name for a Wikimedia Commons user.

                >>> get_userinfo(access_token="…")
                {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._get_json(params={"action": "query", "meta": "userinfo"})

        return resp["query"]["userinfo"]  # type: ignore
