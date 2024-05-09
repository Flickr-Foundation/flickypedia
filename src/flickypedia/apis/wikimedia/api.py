"""
This is an auth-agnostic implementation of some Wikimedia API methods.

Callers are responsible for creating an ``httpx.Client`` instance which
is appropriately authenticated with the Wikimedia API.  This class is
designed to be used with any auth approach.

See https://api.wikimedia.org/wiki/Authentication
"""

import typing

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
