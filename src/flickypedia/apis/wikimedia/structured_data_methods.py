"""
Methods for reading and writing structured data.
"""

import json

from nitrate.types import validate_type

from .base import WikimediaApiBase
from .exceptions import MissingFileException, WikimediaApiException
from ...types.structured_data import ExistingClaims, NewClaims
from ...types.wikimedia import ShortCaption


class StructuredDataMethods(WikimediaApiBase):
    def add_file_caption(self, *, filename: str, caption: ShortCaption) -> str:
        """
        Add a file caption to an image on Wikimedia Commons.

        Returns the M-ID of this file.

        See https://commons.wikimedia.org/wiki/File_captions
        See https://www.wikidata.org/w/api.php?modules=wbsetlabel&action=help

        """
        assert not filename.startswith("File:")

        resp = self._post_json(
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

        resp = self._get_json(
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
            return validate_type(statements, model=ExistingClaims)

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

        resp = self._post_json(
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
