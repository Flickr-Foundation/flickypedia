"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import typing

from flickypedia.types.wikimedia import UserInfo
from .base import HttpxImplementation

from .category_methods import CategoryMethods
from .language_methods import LanguageMethods
from .structured_data_methods import StructuredDataMethods
from .validator_methods import ValidatorMethods
from .wikitext_methods import WikitextMethods
from .upload_methods import UploadMethods


class WikimediaApi(
    HttpxImplementation,
    CategoryMethods,
    LanguageMethods,
    StructuredDataMethods,
    ValidatorMethods,
    WikitextMethods,
    UploadMethods,
):
    def _get(self, params: dict[str, str]) -> typing.Any:
        return self._get_json(params=params)
        return self._request(method="GET", params={**params, "format": "json"})

    def get_userinfo(self) -> UserInfo:
        """
        Returns the user ID and name for a Wikimedia Commons user.

            >>> get_userinfo(access_token="…")
            {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._get(params={"action": "query", "meta": "userinfo"})

        return resp["query"]["userinfo"]  # type: ignore
