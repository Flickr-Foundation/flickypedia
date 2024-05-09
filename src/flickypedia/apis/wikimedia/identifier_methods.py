"""
A file on Wikimedia Commons has two identifiers:

*	A page ID, e.g. "M128"
*	A filename/title, e.g. "File:Herestraat Groningen.JPG"

This file has some methods for converting between the two forms.
"""

import typing

from nitrate.xml import find_required_elem

from .base import WikimediaApiBase
from .exceptions import MissingFileException


class Page(typing.TypedDict):
    pageid: str
    title: str


class IdentifierMethods(WikimediaApiBase):

    # The format of the XML response is:
    #
    #     <?xml version="1.0"?>
    #     <api batchcomplete="">
    #       <query>
    #     	<pages>
    #     	  <page _idx="128" pageid="128" ns="6" title="File:Herestraat Groningen.JPG"/>
    #     	</pages>
    #       </query>
    #     </api>
    #
    # If there is no matching file, the response looks like this:
    #
    #     <page _idx="-1" ns="6" title="File:DefinitelyDoesNotExist.jpg" missing="" />
    #

    def filename_to_id(self, *, filename: str) -> str:
        """
        Given a filename, look up the associated M-ID.

            >>> filename_to_id(filename="File:Herestraat Groningen.JPG")
            "128"

        """
        assert filename.startswith("File:")

        xml = self._get_xml(params={"action": "query", "titles": filename})
        page_elem = find_required_elem(xml, path=".//page")

        try:
            return page_elem.attrib["pageid"]
        except KeyError:
            raise MissingFileException(filename)

    def id_to_filename(self, *, pageid: str) -> str:
        """
        Given a page ID, look up the associated filename.

            >>> id_to_filename(pageid="128")
            "File:Herestraat Groningen.JPG"

        """
        xml = self._get_xml(params={"action": "query", "pageids": pageid})
        page_elem = find_required_elem(xml, path=".//page")

        try:
            return page_elem.attrib["title"]
        except KeyError:
            raise MissingFileException(pageid)
