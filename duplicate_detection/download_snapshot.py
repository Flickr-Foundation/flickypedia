#!/usr/bin/env python3

from html.parser import HTMLParser

import httpx


def find_links(html):
    """
    Given a block of HTML, return a set of all the targets of
    the anchor <a> tags in the HTML.

        >>> find_links('''
            <a href="https://example.net">
            <a href="https://flickr.com/hello">
            <a href="./Cat.jpg">
        ''')
        {'https://example.net', 'https://flickr.com/hello', './Cat.jpg'}

    """
    anchor_targets = set()

    class AnchorParser(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                try:
                    anchor_targets.add(
                        next(value for key, value in attrs if key == "href")
                    )
                except StopIteration:
                    return

    parser = AnchorParser()
    parser.feed(html)

    return anchor_targets


if __name__ == "__main__":
    resp = httpx.get("https://dumps.wikimedia.org/other/wikibase/commonswiki/")
    resp.raise_for_status()

    from pprint import pprint

    pprint(find_links(resp.text))
