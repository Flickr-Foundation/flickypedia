import json

import httpx

from flickypedia.apis.flickr import TakenDateGranularity


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

    def upload_image(self, *, filename, jpeg_url, text):
        """
        Upload an image to Wikimedia Commons.

        See https://www.mediawiki.org/wiki/API:Upload

        """
        upload_resp = self._post(
            data={
                "action": "upload",
                "filename": filename,
                "url": jpeg_url,
                "text": text,
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

    def add_file_caption(self, *, filename, language, value):
        """
        Add a file caption to an image on Wikimedia Commons.

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
            return
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

        See https://commons.wikimedia.org/wiki/Commons:Structured_data
        See https://www.wikidata.org/w/api.php?modules=wbeditentity&action=help

        """
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


class DuplicatePhotoUploadException(WikimediaApiException):
    """
    Thrown when somebody tries to upload a duplicate photo.
    """

    def __init__(self, name):
        super().__init__(f"There is already a photo on Wikimedia Commons called {name}")


def create_wikitext(photo_url, date_taken, flickr_user, license_id):
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.
    """
    # The date is formatted with varying degrees of granularity.
    #
    # For dates which are circa or unknown from the Flickr API, we use
    # two Wikimedia templates for rendering this sort of data.
    #
    # See https://commons.wikimedia.org/wiki/Template:Circa
    # See https://commons.wikimedia.org/wiki/Template:Unknown
    #
    date_format_string = {
        TakenDateGranularity.Second: "%Y-%m-%d %H:%M:%S",
        TakenDateGranularity.Month: "%Y-%m",
        TakenDateGranularity.Year: "%Y",
        TakenDateGranularity.Circa: "{{circa|%Y}}",
    }[date_taken["granularity"]]

    if date_taken["unknown"]:
        date_string = "{{Other date|?}}"
    else:
        date_string = date_taken["value"].strftime(date_format_string)

    return """=={{int:filedesc}}==
{{Information
|Source=[%s]
|Date=%s
|Author=[https://www.flickr.com/people/%s %s]
|Permission=
|other_versions=
}}

=={{int:license-header}}==
{{%s}}
""" % (
        photo_url,
        date_string,
        flickr_user["id"],
        flickr_user["realname"],
        license_id,
    )
