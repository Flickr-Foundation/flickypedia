"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import typing

from flickypedia.types.wikimedia import UserInfo
from .exceptions import (
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
)
from .base import HttpxImplementation

from .category_methods import CategoryMethods
from .language_methods import LanguageMethods
from .structured_data_methods import StructuredDataMethods
from .validator_methods import ValidatorMethods
from .wikitext_methods import WikitextMethods


class WikimediaApi(
    HttpxImplementation,
    CategoryMethods,
    LanguageMethods,
    StructuredDataMethods,
    ValidatorMethods,
    WikitextMethods,
):
    def _get(self, params: dict[str, str]) -> typing.Any:
        return self._get_json(params=params)
        return self._request(method="GET", params={**params, "format": "json"})

    def _post(self, data: dict[str, str], timeout: int | None = None) -> typing.Any:
        return self._post_json(data=data, timeout=timeout)

    def get_userinfo(self) -> UserInfo:
        """
        Returns the user ID and name for a Wikimedia Commons user.

            >>> get_userinfo(access_token="…")
            {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._get(params={"action": "query", "meta": "userinfo"})

        return resp["query"]["userinfo"]  # type: ignore

    def upload_image(self, *, filename: str, original_url: str, text: str) -> str:
        """
        Upload an image to Wikimedia Commons.  Returns the upload filename.

        See https://www.mediawiki.org/wiki/API:Upload

        """
        upload_resp = self._post(
            data={
                "action": "upload",
                "filename": filename,
                "url": original_url,
                "text": text,
                "comment": "Copied photo from Flickr using Flickypedia",
            },
            # Note: this can fail with an httpx.ReadTimeout error with
            # the default timeout, so we increase it.
            timeout=60,
        )

        # Catch an error caused by a file with the same filename already
        # existing on Wikimedia Commons.  Example response:
        #
        #     {
        #       "upload": {
        #         "filekey": "1af50sprx58s.xfatvo.829939.",
        #         "result": "Warning",
        #         "sessionkey": "1af50sprx58s.xfatvo.829939.",
        #         "warnings": {
        #           "exists": "RailwayMuseumClocks.jpg",
        #           "nochange": {"timestamp": "2023-10-10T11:50:11Z"}
        #         }
        #       }
        #     }
        #
        if (
            upload_resp["upload"]["result"] == "Warning"
            and upload_resp["upload"]["warnings"].get("exists") == filename
        ):
            raise DuplicateFilenameUploadException(filename)

        # Catch an error caused by a file which is rejected as a duplicate
        # of a file that already exists on Wikimedia Commons.
        # Example response:
        #
        #     {
        #       "upload": {
        #         "filekey": "1afkfn1e1h2g.cg6fd3.829939.",
        #         "result": "Warning",
        #         "warnings": {"duplicate": ["Yellow_Fin_(6054362864).jpg"]}
        #       }
        #     }
        #
        if (
            upload_resp["upload"]["result"] == "Warning"
            and len(upload_resp["upload"]["warnings"].get("duplicate", [])) == 1
        ):
            raise DuplicatePhotoUploadException(
                upload_resp["upload"]["warnings"]["duplicate"][0]
            )

        # I've never actually seen an upload fail in this way -- it may
        # be that 'Success' and 'Warning' are the only possible results.
        # This branch is here as a defensive measure.
        #
        # If we encounter a case where we get a non-Success/Warning result,
        # we should add a test for it.
        #
        # If we learn that no other result is possible, we should remove
        # this branch and add a comment linking to a reference.
        if upload_resp["upload"]["result"] != "Success":  # pragma: no cover
            raise RuntimeError(f"Unexpected result from upload API: {upload_resp!r}")

        return upload_resp["upload"]["filename"]  # type: ignore
