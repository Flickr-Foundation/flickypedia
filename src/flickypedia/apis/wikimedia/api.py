"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import json
import re
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from flickypedia.utils import validate_typeddict
from flickypedia.apis.structured_data import ExistingClaims, NewClaims
from .exceptions import (
    WikimediaApiException,
    UnknownWikimediaApiException,
    InvalidAccessTokenException,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
)
from .languages import LanguageMatch, order_language_list
from ._types import UserInfo, ShortCaption, TitleValidation


class WikimediaApi:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def _request(
        self,
        *,
        method: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> Any:
        resp = self.client.request(
            method,
            url="https://commons.wikimedia.org/w/api.php",
            params=params,
            data=data,
            timeout=timeout,
        )

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

    def _get(self, params: dict[str, str]) -> Any:
        return self._request(method="GET", params={**params, "format": "json"})

    def _post(self, data: dict[str, str], timeout: int | None = None) -> Any:
        return self._request(
            method="POST",
            data={**data, "format": "json", "token": self.get_csrf_token()},
            timeout=timeout,
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

        return resp["query"]["tokens"]["csrftoken"]  # type: ignore

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

    def add_file_caption(self, *, filename: str, caption: ShortCaption) -> str:
        """
        Add a file caption to an image on Wikimedia Commons.

        Returns the M-ID of this file.

        See https://commons.wikimedia.org/wiki/File_captions
        See https://www.wikidata.org/w/api.php?modules=wbsetlabel&action=help

        """
        assert not filename.startswith("File:")

        resp = self._post(
            data={
                "action": "wbsetlabel",
                "site": "commonswiki",
                "title": f"File:{filename}",
                "language": caption["language"],
                "value": caption["text"],
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
            return resp["entity"]["id"]  # type: ignore
        else:  # pragma: no cover
            raise WikimediaApiException(f"Unexpected response: {resp}")

    def get_structured_data(self, *, filename: str) -> ExistingClaims:
        """
        Retrieve the structured data for a file on Wikimedia Commons.

        This isn't used by Flickypedia directly, but it's very useful for
        debugging and development.  e.g. create some structured data in
        the web interface and then retrieve it with this method to see
        what the JSON looks like.

        See https://commons.wikimedia.org/wiki/Commons:Structured_data
        See https://www.wikidata.org/w/api.php?modules=wbgetentities&action=help

        """
        resp = self._get(
            params={
                "action": "wbgetentities",
                "sites": "commonswiki",
                "titles": f"File:{filename}",
            }
        )

        # This will be an object of the form:
        #
        #     {
        #       "entities": {
        #         "$pageId": {
        #           "statements": {…}
        #         }
        #       }
        #     }
        #
        # We're only interested in the list of statements for now.
        assert len(resp["entities"]) == 1

        statements = list(resp["entities"].values())[0]["statements"]

        if statements == []:
            return {}
        else:
            return validate_typeddict(statements, model=ExistingClaims)

    def add_structured_data(self, *, filename: str, data: NewClaims) -> None:
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
            return None
        else:  # pragma: no cover
            raise WikimediaApiException(f"Unexpected response: {resp}")

    def validate_title(self, title: str) -> TitleValidation:
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

            {'result': 'duplicate|blacklisted|invalid|ok|…'}

        The theory is that at some point we might add additional keys
        to this dictionary, e.g. with more detailed error information.

        """
        assert title.startswith("File:")

        # There's a maximum length of 240 bytes for UTF-8 encoded filenames
        # in Wikimedia Commons.
        #
        # See https://commons.wikimedia.org/wiki/Commons:File_naming#Length
        length_in_bytes = len(title.encode("utf8"))

        if length_in_bytes > 240:
            return {
                "result": "too_long",
                "text": "This title is too long. Please choose a title which is less than 240 bytes.",
            }

        # Check for other pages with this title -- are we going to
        # duplicate an existing file?
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
            return {
                "result": "duplicate",
                "text": (
                    "Please choose a different title. "
                    f"There is already <a href='https://commons.wikimedia.org/wiki/{title}'>a file on Commons</a> with that title."
                ),
            }

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
                return {
                    "result": "invalid",
                    "text": "Please choose a different, more descriptive title.",
                }
            else:  # pragma: no cover
                raise

        if blacklist_resp["titleblacklist"]["result"] != "ok":
            return {
                "result": "blacklisted",
                "text": "Please choose a different, more descriptive title.",
            }

        return {"result": "ok"}

    def find_matching_categories(self, query: str) -> list[str]:
        """
        Return a list of categories that might match this query.

        This can be used to build an autocomplete interface for categories,
        e.g. if the user types "a" we can suggest categories that
        include the letter "a":

            >>> find_matching_categories(query='a')
            ['A',
             'Aircraft of Uzbekistan',
             'Aircraft of Malawi',
             'Aircraft in Portugal',
             'Aircraft in Sierra Leone',
             'Aircraft in Malawi',
             'Architectural elements in Russia',
             'Aircraft in Thailand',
             'Airliners in Russian service',
             'Airliners in Malawian service']

        Note: the results from this API may vary over time, or even
        different requests. For example, there is a test in test_wikimedia.py
        that makes the same query as the example, but returns a slightly
        different set of categories.
        """
        # I found this API action by observing the network traffic in
        # the Upload Wizard.
        #
        # I changed the response format from JSON to XML to give better
        # visiblity into the structure of the response -- the JSON
        # gives an opaque list of lists.
        #
        # See https://www.mediawiki.org/wiki/API:Opensearch
        resp = self.client.request(
            "GET",
            url="https://commons.wikimedia.org/w/api.php",
            params={
                "action": "opensearch",
                "format": "xml",
                "limit": "10",
                "search": query,
                # Here "14" is the namespace for categories; see
                # https://commons.wikimedia.org/wiki/Help:Namespaces
                "namespace": "14",
            },
        )

        xml = ET.fromstring(resp.text)

        # The XML response is of the form:
        #
        #   <?xml version="1.0"?>
        #   <SearchSuggestion xmlns="http://opensearch.org/searchsuggest2" version="2.0">
        #     <Query xml:space="preserve">a</Query>
        #     <Section>
        #       <Item>
        #         <Text xml:space="preserve">Category:A</Text>
        #         <Url xml:space="preserve">https://commons.wikimedia.org/wiki/Category:A</Url>
        #         <Image source="https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/ICS_Alfa.svg/50px-ICS_Alfa.svg.png" width="50" height="50"/>
        #       </Item>
        #       …
        #
        # We're interested in those <Text> values.
        namespaces = {"": "http://opensearch.org/searchsuggest2"}

        return [
            re.sub(r"^Category:", "", text_elem.text)  # type: ignore
            for text_elem in xml.findall(".//Text", namespaces=namespaces)
        ]

    def find_matching_languages(self, query: str) -> list[LanguageMatch]:
        """
        Return a list of languages that might match the query.

        This can be used to build an autocomplete interface for languages,
        e.g. if the user types "es" we can suggest languages that
        include the text "es":

            >>> find_matching_languages(query="es")
            "español"
            "Esperanto"
            "español (formal)"
            "slovenčina [esiruwaku]"
            "slovenščina [esiruwenu]"

        """
        # I found this API action by observing the network traffic in
        # the Upload Wizard when you search for languages while editing
        # the file caption.
        #
        # See https://www.mediawiki.org/wiki/API:Languagesearch
        resp = self._get(
            params={
                "action": "languagesearch",
                "formatversion": "2",
                "search": query,
            }
        )

        return order_language_list(query=query, results=resp["languagesearch"])

    def get_existing_wikitext(self, filename: str) -> str:
        """
        Get the Wikitext for an existing page on Wikimedia.

        See https://www.mediawiki.org/wiki/API:Revisions
        """
        resp = self._get(
            params={
                "action": "query",
                "prop": "revisions",
                "titles": f"File:{filename}",
                "rvlimit": "1",
                "rvslots": "main",
                "rvprop": "content",
            }
        )

        # The response will be wrapped in a dict of the form:
        #
        #     {
        #       'batchcomplete': '',
        #       'query': {
        #         'pages': {'[page ID]': { … data … }}
        #       }
        #     }
        #
        assert len(resp["query"]["pages"]) == 1

        this_page = list(resp["query"]["pages"].values())[0]

        # The data about the individual page is in turn wrapped in
        # a response like:
        #
        #     {'ns': 6,
        #      'pageid': 139134318,
        #      'revisions': [{'slots': {'main': {'*': '… wikitext …'}}}]}
        #
        wikitext = this_page["revisions"][0]["slots"]["main"]["*"]

        assert isinstance(wikitext, str)

        return wikitext

    def add_categories_to_page(self, filename: str, categories: list[str]) -> None:
        """
        Append a list of categories to a page on Wikimedia.

        This method is idempotent; it will only add categories once.
        If a page already has all the categories specified, this is a no-op.

        See https://www.wikidata.org/w/api.php?modules=edit&action=help
        """
        existing_text = self.get_existing_wikitext(filename=filename)

        formatted_categories = [
            f"[[Category:{category_name}]]" for category_name in categories
        ]

        new_categories = [c for c in formatted_categories if c not in existing_text]

        # Prepend a newline, so the new categories appear on newlines,
        # and don't get bunched up with existing categories.
        #
        # TODO: it would be nice to skip this newline if the Wikitext already
        # ends in a newline, but I'm not sure if that's possible.
        new_text = "\n" + "\n".join(new_categories)

        if new_categories:
            self._post(
                data={
                    "action": "edit",
                    "site": "commonswiki",
                    "title": f"File:{filename}",
                    "nocreate": "true",
                    "appendtext": new_text,
                }
            )
