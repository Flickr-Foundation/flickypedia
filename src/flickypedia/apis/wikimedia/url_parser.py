import re

import httpx
import hyperlink

from . import WikimediaApi


def get_filename_from_url(url: str) -> str:
    """
    Given a URL to a file on Commons, return the name of the file.

        >>> get_filename_from_url('https://commons.wikimedia.org/wiki/File:Cat.jpg')
        'Cat.jpg'

    """
    u = hyperlink.DecodedURL.from_text(url)

    if u.host not in {"commons.wikimedia.org", "commons.m.wikimedia.org"}:
        raise ValueError(f"Not a Commons URL: {url!r}")

    # e.g. https://commons.wikimedia.org/?curid=106460733
    if u.path == ("",) and u.get("curid"):
        pageid = u.get("curid")[0]
        assert isinstance(pageid, str)

        api = WikimediaApi(client=httpx.Client())
        filename = api.pageid_to_filename(pageid=pageid)
        return re.sub(r"^File:", "", filename)

    if len(u.path) < 2 or u.path[0] != "wiki" or not u.path[1].startswith("File:"):
        raise ValueError(f"Not a Commons URL: {url!r}")

    return re.sub(r"^File:", "", u.path[1])
