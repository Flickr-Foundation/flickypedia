from .by_url import get_photos_from_flickr
from .comments import (
    create_bot_comment_text,
    create_default_user_comment_text,
)


__all__ = [
    "create_bot_comment_text",
    "create_default_user_comment_text",
    "get_photos_from_flickr",
]
