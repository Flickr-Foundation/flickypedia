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

    def _request(self, *, method, **kwargs):
        try:
            kwargs["params"]["format"] = "json"
        except KeyError:
            kwargs["data"]["format"] = "json"

        resp = self.client.request(method, url="w/api.php", **kwargs)

        # When something goes wrong, we get an ``error`` key in the response.
        #
        # Detect this here and throw an exception, so callers can assume
        # there was no issue if this returns cleanly.
        #
        # See https://www.mediawiki.org/wiki/Wikibase/API#Response
        try:
            error = resp.json()["error"]

            if error["code"] == "mwoauth-invalid-authorization":
                raise InvalidAccessTokenException(error["info"])
            else:
                raise UnknownWikimediaApiException(resp)
        except KeyError:
            pass

        return resp.json()

    def _get(self, **params):
        return self._request(method="GET", params={**params, "format": "json"})

    def _post(self, **data):
        return self._request(
            method="POST",
            data={**data, "format": "json", "token": self.get_csrf_token()},
        )

    def get_csrf_token(self) -> str:
        """
        Get a CSRF token from the Wikimedia API.

        This is required for certain API actions that modify data in
        Wikimedia.  External callers are never expected to use this,
        but functions from this class will call it when they need a token.

        See https://www.mediawiki.org/wiki/API:Tokens
        """
        resp = self._get(action="query", meta="tokens", type="csrf")

        return resp["query"]["tokens"]["csrftoken"]

    def get_userinfo(self) -> str:
        """
        Returns the user ID and name for a Wikimedia Commons user.

            >>> get_userinfo(access_token="…")
            {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._get(action="query", meta="userinfo")

        return resp["query"]["userinfo"]

    def add_file_caption(self, *, filename, language, value):
        """
        Add a file caption to an image on Wikimedia Commons.

        See https://commons.wikimedia.org/wiki/File_captions
        See https://www.wikidata.org/w/api.php?modules=wbsetlabel&action=help

        """
        resp = self._post(
            action="wbsetlabel",
            site="commonswiki",
            title=f"File:{filename}",
            language=language,
            value=value,
        )

        # A successful response from this API looks something like:
        #
        #     {
        #       'entity': {
        #         'id': 'M138765501',
        #         'labels': {
        #           'en': {
        #             'language': 'en',
        #             'value': '…'
        #           }
        #         },
        #         'lastrevid': 811496641,
        #         'type': 'mediainfo'
        #       },
        #       'success': 1
        #     }
        #
        # Reading the MediaWiki API docs, it sounds like any non-zero integer
        # here is fine, so we don't inspect this response too closely --
        # we trust the file caption was set correctly.
        #
        # If we ever see a success=0 response here that doesn't include
        # an error parameter, we can add a test for this branch.
        #
        # See https://www.mediawiki.org/wiki/Wikibase/API#Response
        #
        if resp["success"] != 0:
            return
        else:  # pragma: no cover
            raise WikimediaApiException(f"Unexpected response: {resp}")

    def upload_photo(self, *, photo_url, filename, license, short_caption) -> str:
        """
        Uploads a photo to Wikimedia Commons and adds some structured data.

        See https://www.mediawiki.org/wiki/API:Upload
        """
        # Do the initial upload of the file to Wikimedia Commons.
        #
        # See https://www.mediawiki.org/wiki/API:Upload
        upload_resp = self._request(
            "POST",
            data={
                "action": "upload",
                "filename": filename,
                "url": photo_url,
                "token": self.get_csrf_token(),
                "text": """=={{int:license-header}}==
{{self|%s}}"""
                % license,
            },
            # Note: this can fail with an httpx.ReadTimeout error with
            # the default timeout, so we increase it.
            timeout=60,
        )

        if (
            upload_resp["upload"]["result"] == "Warning"
            and upload_resp["upload"]["warnings"].get("exists") == filename
        ):
            raise DuplicatePhotoUploadException(filename)

        if upload_resp["upload"]["result"] != "Success":
            raise RuntimeError(f"Unexpected result from upload API: {upload_resp!r}")

        # Add some structured data to the file, in particular the
        # "file caption" field.
        #
        # See https://www.wikidata.org/w/api.php?modules=wbsetlabel&action=help
        # See https://www.mediawiki.org/wiki/Wikibase/API
        set_label_resp = self._request(
            "POST",
            data={
                "action": "wbsetlabel",
                "title": f"File:{filename}",
                "site": "commonswiki",
                "value": short_caption,
                # TODO: Support non-English captions
                "language": "en",
                "token": self.get_csrf_token(),
            },
        )

        from pprint import pprint

        pprint(set_label_resp.json())


class WikimediaApiException(Exception):
    pass


<<<<<<< HEAD
class UnknownWikimediaApiException(WikimediaApiException):
=======
class UnknownWikimediaApiException(Exception):
>>>>>>> 9bced5a (Throw a nicer error message when you upload duplicate photos)
    def __init__(self, resp):
        error_info = resp.json()["error"]

        self.code = error_info.get("code")
        self.error_info = error_info
<<<<<<< HEAD
        super().__init__(error_info["info"])


class InvalidAccessTokenException(WikimediaApiException):
    """
    Thrown when we have invalid access credentials.
    """

    pass
=======
        super().__init__(error_info.get("info"))


class DuplicatePhotoUploadException(WikimediaApiException):
    def __init__(self, name):
        super().__init__(f"There is already a photo on Wikimedia Commons called {name}")
>>>>>>> 9bced5a (Throw a nicer error message when you upload duplicate photos)
