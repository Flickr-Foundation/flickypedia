import os

import click

from flickypedia.apis.wikimedia import get_filename_from_url


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos which have already been uploaded to Wikimedia Commons.",
)
def backfillr() -> None:
    pass


@backfillr.command(help="Store cookies for Flickypedia Backfillr Bot")
def store_cookies() -> None:
    """
    Store cookies for Backfillr Bot in the system keychain.

    We rely on pywikibot to do this for us because it can handle the
    Wikimedia Commons login flow, but we don't rely on it to store
    the cookies -- it does so in plain text!

    This is a bit rough and there are deprecation warnings, but it's
    the only way I've found to get cookies that work with the bot=1 flag.
    """
    import json

    import keyring
    import pywikibot
    from pywikibot.comms.http import PywikibotCookieJar

    site = pywikibot.Site("commons", "commons")
    site.login(user="FlickypediaBackfillrBot")

    cookie_jar = PywikibotCookieJar()

    cookie_jar.load(user="FlickypediaBackfillrBot")

    keyring.set_password(
        "flickypedia", "cookies", json.dumps({c.name: c.value for c in cookie_jar})
    )

    os.unlink("pywikibot-FlickypediaBackfillrBot.lwp")


@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    try:
        filename = get_filename_from_url(url)
    except ValueError:
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    print(f"The filename is {filename!r}")
