import json

import httpx


class WikimediaApiBase:
    client: httpx.Client

    def _request(self, *, method, **kwargs):
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

    def _get(self, params):
        return self._request(method="GET", params={**params, "format": "json"})

    def _post(self, data, **kwargs):
        return self._request(
            method="POST",
            data={**data, "format": "json", "token": self.get_csrf_token()},
            **kwargs,
        )


class WikimediaApi(WikimediaApiBase):
    """
    This is a thin wrapper for calling the Wikimedia API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the error handling in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, access_token, user_agent):
        self.client = httpx.Client(
            base_url="https://commons.wikimedia.org",
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": user_agent,
            },
        )

    def get_csrf_token(self) -> str:
        """
        Get a CSRF token from the Wikimedia API.

        This is required for certain API actions that modify data in
        Wikimedia.  External callers are never expected to use this,
        but functions from this class will call it when they need a token.

        See https://www.mediawiki.org/wiki/API:Tokens
        """
        resp = self._get(params={"action": "query", "meta": "tokens", "type": "csrf"})

        return resp["query"]["tokens"]["csrftoken"]

    def get_userinfo(self) -> str:
        """
        Returns the user ID and name for a Wikimedia Commons user.

            >>> get_userinfo(access_token="…")
            {"id": 829939, "name": "Alexwlchan"}

        See https://www.mediawiki.org/wiki/API:Userinfo

        """
        resp = self._get(params={"action": "query", "meta": "userinfo"})

        return resp["query"]["userinfo"]

    def upload_image(self, *, filename: str, original_url: str, text: str):
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

        return upload_resp["upload"]["filename"]

    def add_file_caption(self, *, filename, language, value):
        """
        Add a file caption to an image on Wikimedia Commons.

        Returns the M-ID of this file.

        See https://commons.wikimedia.org/wiki/File_captions
        See https://www.wikidata.org/w/api.php?modules=wbsetlabel&action=help

        """
        resp = self._post(
            data={
                "action": "wbsetlabel",
                "site": "commonswiki",
                "title": f"File:{filename}",
                "language": language,
                "value": value,
            }
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
            return resp["entity"]["id"]
        else:  # pragma: no cover
            raise WikimediaApiException(f"Unexpected response: {resp}")

    def get_structured_data(self, *, filename):
        """
        Retrieve the structured data for a file on Wikimedia Commons.

        This isn't used by Flickypedia directly, but it's very useful for
        debugging and development.  e.g. create some structured data in
        the web interface and then retrieve it with this method to see
        what the JSON looks like.

        See https://commons.wikimedia.org/wiki/Commons:Structured_data
        See https://www.wikidata.org/w/api.php?modules=wbgetentities&action=help

        """
        return self._get(
            params={
                "action": "wbgetentities",
                "sites": "commonswiki",
                "titles": f"File:{filename}",
            }
        )

    def add_structured_data(self, *, filename, data):
        """
        Add some structured data to a file on Wikimedia Commons.

        This is a relatively crude tool -- it will simply insert new
        statements, and ignore what's already there.  It would be nice
        if we could query the existing statements and not duplicate
        information, but that's a problem for another time.

        In Flickypedia, this expects to receive an object with
        a single key "claims", e.g.

            {
              "claims": [
                {
                  "mainsnak": {
                    "snaktype": "value",
                    "property": "P56",
                    "datavalue": {
                      "value": "ExampleString",
                      "type": "string"
                    }
                  },
                  "type": "statement",
                  "rank": "normal"
                }
              ]
            }

        See https://commons.wikimedia.org/wiki/Commons:Structured_data
        See https://www.wikidata.org/w/api.php?modules=wbeditentity&action=help

        """
        # Do some basic validation of the input format here -- if you
        # pass the wrong data into the Wikimedia API, the error message
        # is utterly unhelpful.
        #
        # e.g. when I passed in the list of claims as data=[…] instead of
        # wrapping it in an object data={'claims': […]}, I got this error
        # message from the API:
        #
        #     {
        #       'code': 'not-recognized-string',
        #       'info': 'A string was expected, but not recognized.',
        #       'messages': [
        #         {
        #           'name': 'wikibase-api-not-recognized-string',
        #           …
        #         }
        #       ]
        #     }
        #
        if (
            not isinstance(data, dict)
            or data.keys() != {"claims"}
            or not isinstance(data["claims"], list)
        ):
            raise TypeError

        resp = self._post(
            data={
                "action": "wbeditentity",
                "site": "commonswiki",
                "title": f"File:{filename}",
                "data": json.dumps(data),
            }
        )

        if resp["success"] != 0:
            return
        else:  # pragma: no cover
            raise WikimediaApiException(f"Unexpected response: {resp}")


class WikimediaPublicApi(WikimediaApiBase):
    def __init__(self, user_agent):
        self.client = httpx.Client(
            base_url="https://commons.wikimedia.org",
            headers={"User-Agent": user_agent},
        )

    def validate_title(self, title: str):
        """
        Given the name of a title, check whether it's allowed as
        a title for a new file on Wikimedia Commons.

        We try to rely on the Wikimedia APIs to do this for us, rather
        than duplicating their logic -- it's slower, but it saves us
        from having to maintain our own copy of the logic (which would
        inevitably be slightly wrong or broken).

        Instead, we do similar checks to the File Upload Wizard.
        I opened the Upload Wizard in my browser, then I used the
        developer tools to observe the API requests going back and
        forth to check whether the title was okay.

        The current result from this function is always a dict like:

            {'result': 'duplicate|blacklisted|invalid|ok'}

        The theory is that at some point we might add additional keys
        to this dictionary, e.g. with more detailed error information.

        """
        assert title.startswith("File:")

        # First check for other pages with this title -- are we going
        # to duplicate an existing file?
        #
        # If the file exists, we'll get the ID of the existing page in
        # the `pages` list in the response:
        #
        #     {"query": {"pages": {"139632053": {…}}}}
        #
        # If the file doesn't exist, we'll get "-1" as the ID:
        #
        #     {"query": {"pages": {"-1": {…}}}}
        #
        existing_title_resp = self._get(
            params={"action": "query", "titles": title, "prop": "info"}
        )

        if existing_title_resp["query"]["pages"].keys() != {"-1"}:
            return {"result": "duplicate"}

        # Second check to see if the title is blocked.
        #
        # This could be if e.g. the title is too long, or too short, or
        # contains forbidden characters.
        #
        # If the title is blacklisted, we'll get a response like:
        #
        #     {
        #       "titleblacklist": {
        #         "result": "blacklisted",
        #         "reason":"<p>The file name you were trying to upload
        #                   has been [[c:MediaWiki:Titleblacklist|blacklisted]]
        #                   because it is very common, uninformative, or
        #                   spelled in ALLCAPS.
        #       …
        #     }
        #
        # If the title is invalid, we'll get a response like:
        #
        #     {
        #       "error": {
        #         "code": "invalidtitle",
        #         "info":"Bad title \"File:\".",
        #         …
        #     }
        #
        # If the title is allowed, we'll get a response:
        #
        #     {"titleblacklist":{"result":"ok"}}
        #
        # See https://www.mediawiki.org/wiki/Extension:TitleBlacklist#Testing_for_matches
        # See https://www.mediawiki.org/w/api.php?action=help&modules=titleblacklist
        #
        try:
            blacklist_resp = self._get(
                params={
                    "action": "titleblacklist",
                    "tbaction": "create",
                    "tbtitle": title,
                }
            )
        except UnknownWikimediaApiException as exc:
            if exc.code == "invalidtitle":
                return {"result": "invalid"}
            else:  # pragma: no cover
                raise

        if blacklist_resp["titleblacklist"]["result"] != "ok":
            return {"result": "blacklisted"}

        return {"result": "ok"}


class WikimediaApiException(Exception):
    pass


class UnknownWikimediaApiException(WikimediaApiException):
    def __init__(self, resp):
        error_info = resp.json()["error"]

        self.code = error_info.get("code")
        self.error_info = error_info
        super().__init__(error_info["info"])


class InvalidAccessTokenException(WikimediaApiException):
    """
    Thrown when we have invalid access credentials.
    """

    pass


class DuplicateFilenameUploadException(WikimediaApiException):
    """
    Thrown when somebody tries to upload a photo which has the same
    file as a file already on Wikimedia Commons.
    """

    def __init__(self, filename):
        self.filename = filename
        super().__init__(
            f"There is already a photo on Wikimedia Commons called {filename}"
        )


class DuplicatePhotoUploadException(WikimediaApiException):
    """
    Thrown when somebody tries to upload a photo which is identical to
    an existing photo.
    """

    def __init__(self, filename):
        self.filename = filename
        super().__init__(
            f"There is already an identical photo on Wikimedia Commons ({filename})"
        )
