"""
Methods for dealing with Wikitext.
"""

from .base import WikimediaApiBase
from .exceptions import MissingFileException, UnknownWikimediaApiException


class WikitextMethods(WikimediaApiBase):
    def get_wikitext(self, *, filename: str) -> str:
        """
        Return the Wikitext for this page, if it exists.

        See https://www.mediawiki.org/wiki/API:Parsing_wikitext
        """
        assert filename.startswith("File:")

        try:
            resp = self._get_json(
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

    def purge_wikitext(self, *, filename: str) -> None:
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
        self._post_json(
            data={
                "action": "purge",
                "site": "commonswiki",
                "title": f"File:{filename}",
                "summary": "Flickypedia edit (purge to force re-render of {{Information}} template with new structured data)",
            }
        )
