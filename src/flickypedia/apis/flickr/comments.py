import textwrap

from flickr_photos_api import FlickrApi


def create_bot_comment_text(
    user_name: str, user_url: str, wikimedia_page_title: str
) -> str:
    """
    Creates the comment posted by Flickypedia Bot.

    We don't allow users to change this text.
    """
    assert wikimedia_page_title.startswith("File:")

    return textwrap.dedent(
        f"""
        Hi, I’m <a href="https://www.flickr.com/people/flickypedia">Flickypedia Bot</a>.

        A Wikimedia Commons user named <a href="{user_url}">{user_name}</a> has uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>.

        <a href="https://commons.wikimedia.org/wiki/{wikimedia_page_title}">Would you like to see</a>? We hope you like it!
    """
    ).strip()


def create_default_user_comment_text(wikimedia_page_title: str) -> str:
    """
    Creates the default text for a user's comment.
    """
    assert wikimedia_page_title.startswith("File:")

    return textwrap.dedent(
        f"""
        Hi, I’ve uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>. <a href="https://commons.wikimedia.org/wiki/{wikimedia_page_title}">Would you like to see</a>?

        I hope you like it!
    """
    ).strip()


def post_bot_comment(
    user_name: str, user_url: str, photo_id: str, wikimedia_page_title: str
) -> str:
    """
    Post a comment as Flickypedia bot.

    We don't allow users to change this text, so we just take a few
    parameters and build it from a template, rather than taking text
    passed from the page itself.
    """
    # Note: this is here rather than at the top-level to avoid issues
    # with circular imports.
    from flickypedia.uploadr.auth.flickr import get_flickypedia_bot_oauth_client

    client = get_flickypedia_bot_oauth_client()
    api = FlickrApi(client=client)

    comment_text = create_bot_comment_text(
        user_name=user_name,
        user_url=user_url,
        wikimedia_page_title=wikimedia_page_title,
    )

    comment_id = api.post_comment(photo_id=photo_id, comment_text=comment_text)

    return comment_id
