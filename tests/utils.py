import re


def minify(text: str) -> str:
    """
    Minify an HTML string.  This means compacting long runs of whitespace,
    e.g.

        >>> html = "this album\n is created\n from a Jinja2 template"
        >>> "this album is created" in html
        False
        >>> "this album is created" in minify(html)
        True

    It's meant for use in tests -- this may not be a perfect minifier,
    but it's good enough for our test assertions.
    """
    return re.sub(r"\s+", " ", text).strip()
