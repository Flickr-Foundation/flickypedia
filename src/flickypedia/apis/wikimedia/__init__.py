from .exceptions import (
    WikimediaApiException,
    UnknownWikimediaApiException,
    InvalidAccessTokenException,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    MissingFileException,
)
from .language_methods import top_n_languages, LanguageMatch
from .url_parser import get_filename_from_url

from .base import HttpxImplementation

from .category_methods import CategoryMethods
from .language_methods import LanguageMethods
from .structured_data_methods import StructuredDataMethods
from .validator_methods import ValidatorMethods
from .wikitext_methods import WikitextMethods
from .upload_methods import UploadMethods
from .user_methods import UserMethods


class WikimediaApi(
    HttpxImplementation,
    CategoryMethods,
    LanguageMethods,
    StructuredDataMethods,
    ValidatorMethods,
    WikitextMethods,
    UploadMethods,
    UserMethods,
):
    pass


__all__ = [
    "DuplicateFilenameUploadException",
    "DuplicatePhotoUploadException",
    "get_filename_from_url",
    "InvalidAccessTokenException",
    "LanguageMatch",
    "MissingFileException",
    "UnknownWikimediaApiException",
    "WikimediaApi",
    "WikimediaApiException",
    "top_n_languages",
]
