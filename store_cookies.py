"""
Store some cookies for FlickypediaBackfillrBot to use.
"""

import json

import keyring
import pywikibot
from pywikibot.comms.http import PywikibotCookieJar


if __name__ == "__main__":
    site = pywikibot.Site("commons", "commons")
    site.login(user="FlickypediaBackfillrBot")

    cookie_jar = PywikibotCookieJar()

    cookies = cookie_jar.load(user="FlickypediaBackfillrBot")

    keyring.set_password(
        "flickypedia", "cookies", json.dumps({c.name: c.value for c in cookie_jar})
    )
