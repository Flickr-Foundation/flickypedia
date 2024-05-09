"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import re
import typing
from xml.etree import ElementTree as ET

from flickypedia.types.wikimedia import UserInfo
from flickypedia.utils import find_required_elem
from .exceptions import (
    UnknownWikimediaApiException,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    MissingFileException,
)
from .base import HttpxImplementation
from .languages import LanguageMatch, order_language_list

from .structured_data_methods import StructuredDataMethods
from .validator_methods import ValidatorMethods


class WikimediaApi(HttpxImplementation, StructuredDataMethods, ValidatorMethods):
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
