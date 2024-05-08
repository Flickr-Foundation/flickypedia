"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import json
import re
import typing
from xml.etree import ElementTree as ET

import httpx

from flickypedia.types import validate_typeddict
from flickypedia.types.structured_data import ExistingClaims, NewClaims
from flickypedia.types.wikimedia import UserInfo, ShortCaption, TitleValidation
from flickypedia.utils import find_required_elem
from .exceptions import (
    WikimediaApiException,
    UnknownWikimediaApiException,
    InvalidAccessTokenException,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    MissingFileException,
)
from .languages import LanguageMatch, order_language_list


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
    ) -> typing.Any:
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

    def _get(self, params: dict[str, str]) -> typing.Any:
        return self._request(method="GET", params={**params, "format": "json"})

    def _post(self, data: dict[str, str], timeout: int | None = None) -> typing.Any:
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
                "summary": "Flickypedia edit (add caption)",
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
        assert not filename.startswith("File:")

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

        page = list(resp["entities"].values())[0]

        # If the file exists but it doesn't have any structured data, we'll
        # get a response of the form:
        #
        #     {'id': 'M1004', 'missing': ''}
        #
        # Because Commons has been able to resolve this filename to an ID,
        # we know the page exists, it just doesn't have any SDC statements.
        # We can return an empty dict here.
        if "missing" in page and "id" in page:
            return {}

        # If the file doesn't exist on Commons, we'll get a response of
        # the form:
        #
        #     {'missing': '',
        #      'site': 'commonswiki',
        #      'title': 'File:DefinitelyDoesNotExist.jpg'}
        #
        if "missing" in page:
            raise MissingFileException(filename)

        # Otherwise, we got some statements back to Commons, which we
        # need to turn into a useful response.
        #
        # Note that we can still get an empty list of statements here --
        # I don't know how this is different from the "file exists but no SDC"
        # case above, or why sometimes we get an error and sometimes an
        # empty list.  :-/
        #
        # There are tests for both cases if you want to see example responses.
        statements = list(resp["entities"].values())[0]["statements"]

        if statements == []:
            return {}
        else:
            return validate_typeddict(statements, model=ExistingClaims)

    def add_structured_data(
        self, *, filename: str, data: NewClaims, summary: str
    ) -> None:
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
                "summary": summary,
                "tags": "BotSDC",
                "maxlag": "2",
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

        # Check to see if the user has added their own suffix to the
        # filename, as well as the one we've added automatically.
        #
        # Wikimedia Commons will reject a file named this way with a slightly
        # unhelpful message; let's provide a better one.
        base_name = title.replace("File:", "").rsplit(".", 1)[0]

        if base_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff")
        ):
            return {
                "result": "invalid",
                "text": "Please remove the filename suffix; it will be added automatically.",
            }

        # Check for illegal characters, as defined by the wgIllegalFileChars
        # setting -- these are blocked by the Upload Wizard.
        #
        # See https://www.mediawiki.org/wiki/Manual:$wgIllegalFileChars
        # See https://til.alexwlchan.net/wmc-allowed-title-characters/
        if any(char in base_name for char in ":/\\"):
            return {
                "result": "invalid",
                "text": "This title is invalid. Make sure to remove characters like square brackets, colons, slashes, comparison operators, pipes and curly brackets.",
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

        # Do a match for other pages with an equivalent filename -- the
        # title search in the previous test is case-sensitive.
        #
        # e.g. if there's an existing file called "Cat.JPG", then you can't
        # upload a new file called "Cat.jpg".
        #
        # Note that we do a slightly different search from the Wikimedia
        # Upload Wizard -- it uses the ``query`` action, but we use the
        # ``opensearch`` action to do case insensitive searches.
        #
        # See https://en.wikipedia.org/wiki/Wikipedia:File_names
        #
        base_title, _ = title.replace("File:", "").rsplit(".", 1)
        opensearch_resp = self.client.request(
            "GET",
            url="https://commons.wikimedia.org/w/api.php",
            params={
                "action": "opensearch",
                "format": "xml",
                "limit": "10",
                "search": base_title,
                # Here "14" is the namespace for categories; see
                # https://commons.wikimedia.org/wiki/Help:Namespaces
                "namespace": "6",
            },
        )

        xml = ET.fromstring(opensearch_resp.text)

        # The XML response is of the form:
        #
        #     <SearchSuggestion xmlns="http://opensearch.org/searchsuggest2" version="2.0">
        #       <Query xml:space="preserve">tower Bridge at Night</Query>
        #       <Section>
        #         <Item>
        #           <Text xml:space="preserve">File:Tower Bridge at night (32658848243).jpg</Text>
        #           …
        #         </Item>
        #         <Item>…</Item>
        #         <Item>…</Item>
        #
        # We're interested in looking for <Text> elements with a filename
        # that matches ours, but case-insensitive.
        namespaces = {"": "http://opensearch.org/searchsuggest2"}

        for text_elem in xml.findall(".//Text", namespaces=namespaces):
            this_filename = text_elem.text
            assert this_filename is not None

            if this_filename.lower() == title.lower():
                return {
                    "result": "duplicate",
                    "text": (
                        "Please choose a different title. "
                        f"There is already a file <a href='https://commons.wikimedia.org/wiki/{this_filename}'>{this_filename.replace('File:', '')}</a> on Commons."
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
        # visibility into the structure of the response -- the JSON
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

        This API is aware of many labels for languages, so you can can
        search by alternative names for the same language:

            >>> find_matching_languages(query="spani")
            "spanish / español"
            "spanish (formal address) / español (formal)"
            "spanishgbe (latin america) / español de América Latina"

        """
        assert len(query) > 0

        # I found this API action by observing the network traffic in
        # the Upload Wizard when you search for languages while editing
        # the file caption.
        #
        # See https://www.mediawiki.org/wiki/API:Languagesearch
        resp = self.client.request(
            "GET",
            url="https://commons.wikimedia.org/w/api.php",
            params={
                "action": "languagesearch",
                "format": "xml",
                "search": query,
            },
        )

        xml = ET.fromstring(resp.text)

        # The response is a block of XML of the form:
        #
        #     <api>
        #       <languagesearch gu="gujarati" gaa="ga" gcr="guianan creole" …/>
        #     </api>
        #
        languagesearch = find_required_elem(xml, path=".//languagesearch")

        return order_language_list(query=query, results=languagesearch.attrib)

    def get_wikitext(self, filename: str) -> str:
        """
        Return the Wikitext for this page, if it exists.

        See https://www.mediawiki.org/wiki/API:Parsing_wikitext
        """
        assert filename.startswith("File:")

        try:
            resp = self._get(
                params={
                    "action": "parse",
                    "page": filename,
                    "prop": "text",
                },
            )
        except UnknownWikimediaApiException as exc:
            if exc.code == "missingtitle":
                raise MissingFileException(filename)
            else:
                raise

        text = resp["parse"]["text"]["*"]
        assert isinstance(text, str)

        return text

    def force_sdc_rerender(self, filename: str) -> None:
        """
        Force Wikimedia to re-render the SDC in the page.

        We use the Lua-driven {{Information}} template in the Wikitext,
        which is populated by structured data -- but the timing can
        cause some confusing behaviour:

        1.  We upload the initial photo.  This includes the {{Information}}
            template, but it's empty because there's no SDC yet.
        2.  We set some SDC on the photo.  This puts a job on a background
            queue to re-render the {{Information}} template, but this can
            take a while.
        3.  The user clicks to see their new photo, but the Information table
            on the page is empty because it hasn't been re-rendered with
            the SDC yet.  What happened?!

        This function does a no-op edit to force an immediate re-render
        of the page, including the SDC-driven templates.
        """
        self._post(
            data={
                "action": "purge",
                "site": "commonswiki",
                "title": f"File:{filename}",
                "summary": "Flickypedia edit (purge to force re-render of {{Information}} template with new structured data)",
            }
        )
