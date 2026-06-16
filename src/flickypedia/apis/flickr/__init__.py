from .by_url import get_photos_from_flickr
from .comments import (
    create_bot_comment_text,
    create_default_user_comment_text,
)
from .patches import apply_flickr_api_patches
from .single_photo_methods import get_single_photo

apply_flickr_api_patches()

__all__ = [
    "create_bot_comment_text",
    "create_default_user_comment_text",
    "get_photos_from_flickr",
    "get_single_photo",
]
