"""
Methods for reading and writing structured data.
"""

from .base import WikimediaApiBase
from .exceptions import WikimediaApiException
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
