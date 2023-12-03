import functools

from flask import abort, jsonify, request
from flask_login import current_user, login_required

from flickypedia.apis.wikimedia import top_n_languages, LanguageMatch
from ._types import ViewResponse


@login_required
def validate_title_api() -> ViewResponse:
    """
    A basic API for title validation that can be called from JS on the page.

    This allows us to have a single definition of title validation
    which is shared by client and server-side checks.
    """
    try:
        title = request.args["title"]
    except KeyError:
        abort(400)

    if not title.startswith("File:"):
        abort(400)

    api = current_user.wikimedia_api()
    result = api.validate_title(title)

    return jsonify(result)


@functools.lru_cache(maxsize=128)
def find_matching_categories(query: str) -> list[str]:
    """
    Find matching categories.  Because this is a read-only query on the
    global Wikimedia namespace, we cache the results of this lookup across
    all Flickypedia users.
    """
    api = current_user.wikimedia_api()
    result = api.find_matching_categories(query)
    return result


@login_required
def find_matching_categories_api() -> ViewResponse:
    """
    A basic API for looking up matching categories that can be called
    from JS on the page.
    """
    query = request.args.get("query")

    if not query:
        abort(400)

    result = find_matching_categories(query)

    return jsonify(result)


@functools.lru_cache(maxsize=128)
def find_matching_languages(query: str) -> list[LanguageMatch]:
    """
    Find matching languages.  Because this is a read-only query on the
    global Wikimedia namespace, we cache the results of this lookup across
    all Flickypedia users.
    """
    api = current_user.wikimedia_api()
    result = api.find_matching_languages(query)
    return result


def find_matching_languages_api() -> ViewResponse:
    """
    A basic API for looking up matching languages that can be called
    from JS on the page.
    """
    query = request.args.get("query")

    if not query:
        return jsonify(
            [
                {"id": lang_id, "label": label, "match_text": None}
                for lang_id, label in top_n_languages(n=10)
            ]
        )

    result = find_matching_languages(query)

    return jsonify(result)
