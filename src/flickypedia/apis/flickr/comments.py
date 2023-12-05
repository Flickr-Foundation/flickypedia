"""
This file has some code for posting comments to Flickr.
"""

import xml.etree.ElementTree as ET

import httpx

from flickypedia.utils import find_required_elem
from .exceptions import FlickrApiException, InsufficientPermissionsToComment


class FlickrCommentsApi:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def post_comment(self, photo_id: str, comment_text: str) -> str:
        """
        Post a comment to Flickr.

        Returns the ID of the newly created comment.

        Note that Flickr comments are idempotent, so we don't need to worry
        too much about double-posting in this method.  If somebody posts
        the same comment twice, Flickr silently discards the second and
        returns the ID of the original comment.
        """
        resp = self.client.post(
            "https://api.flickr.com/services/rest/",
            params={
                "method": "flickr.photos.comments.addComment",
                "photo_id": photo_id,
                "comment_text": comment_text,
            },
        )

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = ET.fromstring(resp.text)

        # If the Flickr API call fails, it will return a block of XML like:
        #
        #       <rsp stat="fail">
        #       	<err
        #               code="1"
        #               msg="Photo &quot;1211111111111111&quot; not found (invalid ID)"
        #           />
        #       </rsp>
        #
        if xml.attrib["stat"] == "fail":
            errors = find_required_elem(xml, path=".//err").attrib

            if errors["code"] == "99":
                raise InsufficientPermissionsToComment()
            else:
                raise FlickrApiException(errors)

        return find_required_elem(xml, path=".//comment").attrib["id"]
