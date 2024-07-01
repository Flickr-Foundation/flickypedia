import json
import os

import click
from flickr_photos_api import FlickrApi
import httpx
import keyring
import termcolor

from flickypedia.apis.wikimedia import get_filename_from_url, WikimediaApi
from .backfillr import Backfillr


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
@click.argument("URLS", nargs=-1)
def update_files(urls: list[str]) -> None:
    flickr_api = FlickrApi.with_api_key(
        api_key=keyring.get_password("flickr_api", "key"),
        user_agent="Alex Chan's personal scripts <alex@alexwlchan.net>",
    )

    backfillr = Backfillr(
        flickr_api=flickr_api,
        wikimedia_api=WikimediaApi(
            client=httpx.Client(
                cookies=json.loads(keyring.get_password("flickypedia", "cookies"))
            )
        ),
    )

    for u in urls:
        try:
            filename = get_filename_from_url(u)
        except ValueError:
            raise click.UsageError(
                f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {u!r}"
            )

        actions = backfillr.update_file(filename=filename)

        print(filename)
        for a in actions:
            print(a['property_id'].ljust(8), end='')

            if a['action'] == 'do_nothing':
                print('do nothing')
            elif a['action'] == 'add_missing':
                print(termcolor.colored(a['action'], 'green'))
            else:
                print(termcolor.colored(a['action'], 'red'))

        print("")
