import click


@click.group(
    short_help="Commands for the web app for copying photos from Flickr to Wikimedia",
    help="Commands for the web app for copying openly-licensed photos from Flickr to Wikimedia Commons.",
)
def uploadr() -> None:
    pass


@uploadr.command(short_help="Store an OAuth token for the Flickypedia Bot user.")
def store_flickypedia_bot_token() -> None:
    from .auth import store_flickypedia_user_oauth_token

    store_flickypedia_user_oauth_token()
