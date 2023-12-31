import re

import hyperlink


def get_filename_from_url(url: str) -> str:
    """
    Given a URL to a file on Commons, return the name of the file.

        >>> get_filename_from_url('https://commons.wikimedia.org/wiki/File:Cat.jpg')
        'Cat.jpg'

    """
    u = hyperlink.DecodedURL.from_text(url)

    if u.host not in {"commons.wikimedia.org", "commons.m.wikimedia.org"}:
        raise ValueError(f"Not a Commons URL: {url!r}")

    if len(u.path) < 2 or u.path[0] != "wiki" or not u.path[1].startswith("File:"):
        raise ValueError(f"Not a Commons URL: {url!r}")

    return re.sub(r"^File:", "", u.path[1])
