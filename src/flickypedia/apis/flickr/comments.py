import pathlib
import xml.etree.ElementTree as ET

import httpx

from flickypedia.uploadr.auth import WikimediaUserSession
from flickypedia.uploadr.auth.flickr import get_flickypedia_bot_oauth_client
from flickypedia.utils import find_required_text
from .exceptions import InsufficientPermissionsToComment


class FlickrCommentsApi:
    """
    This is a client
    """
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def post_comment(self, photo_id: str, comment_text: str) -> str:
        """
        Post a comment to Flickr.

        Returns the ID of the newly created comment.
        """
        resp = self.client.post(
            "https://api.flickr.com/services/rest/",
            params={
                "method": "flickr.photos.comments.addComment",
                "photo_id": photo_id,
                "comment_text": comment_text
            }
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
        # Different API endpoints have different codes, and so we just throw
        # and let calling functions decide how to handle it.
        if xml.attrib["stat"] == "fail":
            errors = find_required_elem(xml, path=".//err").attrib

            if errors["code"] == "99":
                raise InsufficientPermissionsToComment()
            else:
                raise FlickrApiException(errors)

        return find_required_elem(resp, match=".//comment").attrib["id"]


def create_bot_comment(user: WikimediaUserSession, photo_id: str, wikimedia_title: str) -> str:
    """
    Creates the comment posted by Flickypedia Bot.

    We don't allow users to change this text.
    """
    return textwrap.dedent("""
        Hi, I’m <a href="https://www.flickr.com/people/flickypedia">Flickypedia Bot</a>.

        A Wikimedia Commons user named <a href="{user.profile_url}">{user.name}</a> has uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>.

        <a href="https://commons.wikimedia.org/wiki/File:{wikimedia_title}">Would you like to see</a>? We hope you like it!
    """).strip()


def post_bot_comment():
    client = get_flickypedia_bot_oauth_client()
    api = FlickrCommentsApi(client)

    comment_id = api.post_comment(
        photo_id='53374767803',
        comment_text='This is yet another comment posted by Flickypedia bot'
    )

    return comment_id
