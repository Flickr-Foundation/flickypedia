"""
Everything related to user authentication.

In particular, this module should contain all the code related to users
authenticating with the Wikimedia and Flickr API.  The goal is to keep
this all in one place so it can be considered and reviewed as a single
unit -- this is the most sensitive code in the app.
"""

from .flickr import get_flickypedia_bot_oauth_client, store_flickypedia_user_oauth_token
from .wikimedia import (
    load_user,
    login,
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
    SESSION_ENCRYPTION_KEY,
    user_db,
    WikimediaUserSession,
)

__all__ = [
    "get_flickypedia_bot_oauth_client",
    "load_user",
    "login",
    "logout",
    "oauth2_authorize_wikimedia",
    "oauth2_callback_wikimedia",
    "SESSION_ENCRYPTION_KEY",
    "store_flickypedia_user_oauth_token",
    "user_db",
    "WikimediaUserSession",
]
