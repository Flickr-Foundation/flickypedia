import os
import pathlib
import typing
import keyring


def create_config(data_directory: pathlib.Path) -> dict[str, typing.Any]:
    """
    Create the config for Flickypedia.

    Flickypedia writes a number of temporary files as part of its work.
    The ``data_directory`` is their root.
    """

    # This application uses a mix of keyring and environment variables for
    # secrets, sometimes for the same secrets. The tests require the ability to
    # override the secrets in the environment variables to function. In order
    # to avoid changes across the codebase while moving this to run under
    # systemd we fall back on loading the environment variables from the
    # keyring here, allowing this to be started without systemd needing to
    # execute the keychain to populate them as environment variables.
    ENVIRON_KEYRING_MAP = {
        "FLICKR_CLIENT_ID": "api_key",
        "FLICKR_CLIENT_SECRET": "api_secret",
        "FLICKR_API_KEY": "flickr_api_key",
        "WIKIMEDIA_CLIENT_ID": "wikimedia_client_id",
        "WIKIMEDIA_CLIENT_SECRET": "wikimedia_client_secret",
    }
    for ev, kv in ENVIRON_KEYRING_MAP.items():
        if ev not in os.environ:
            password = keyring.get_password("flickypedia", kv)
            if password is None:
                raise RuntimeError(f"Could not retrieve password {ev} from the environment, or from keyring (flickypedia, {kv})")
            os.environ[ev] = password

    # Implementation note: although these URLs are currently hard-coded,
    # there is a beta cluster we might use in the future.  It's currently
    # broken, so we're not adding support for it yet, but we could if
    # it ever gets fixed.
    #
    # See https://github.com/Flickr-Foundation/flickypedia/issues/4
    wikimedia_oauth2 = {
        "client_id": os.environ.get("WIKIMEDIA_CLIENT_ID"),
        "client_secret": os.environ.get("WIKIMEDIA_CLIENT_SECRET"),
        "authorize_url": "https://meta.wikimedia.org/w/rest.php/oauth2/authorize",
        "token_url": "https://meta.wikimedia.org/w/rest.php/oauth2/access_token",
    }

    flickr_oauth1 = {
        "client_id": os.environ.get("FLICKR_CLIENT_ID"),
        "client_secret": os.environ.get("FLICKR_CLIENT_SECRET"),
        "request_url": "https://www.flickr.com/services/oauth/request_token",
        "token_url": "https://www.flickr.com/services/oauth/access_token",
    }

    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY") or "you-will-never-guess",
        "FLICKR_API_KEY": os.environ.get("FLICKR_API_KEY", "<UNKNOWN>"),
        #
        # TODO: Get this into the data directory.
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{data_directory.absolute()}/db.sqlite",
        #
        # The directory for the upload queue.
        "UPLOAD_QUEUE_DIRECTORY": data_directory / "queue" / "uploads",
        #
        # Used as a temporary cache for responses from the Flickr API.
        #
        # We can save results in here, and pass the filename around in the
        # user session.  This is just public data from the Flickr API,
        # so there's nothing sensitive in here.
        "FLICKR_API_RESPONSE_CACHE": data_directory / "flickr_api_cache",
        #
        # Used as a directory to find SQLite databases which contain information
        # about duplicates.
        "DUPLICATE_DATABASE_DIRECTORY": data_directory / "duplicates",
        #
        # Hard-coded values for OAuth 2 providers.
        "OAUTH_PROVIDERS": {
            "wikimedia": wikimedia_oauth2,
            "flickr": flickr_oauth1,
        },
        #
        # The IDs of licenses that we can upload to Flickypedia.
        "ALLOWED_LICENSES": {
            "cc-by-2.0",
            "cc-by-sa-2.0",
            "cc-by-4.0",
            "cc-by-sa-4.0",
            "usgov",
            "cc0-1.0",
            "pdm",
        },
        #
        # The number of photos to show on a single page
        "PHOTOS_PER_PAGE": 100,
        #
        # A User-Agent sent on HTTP requests
        "USER_AGENT": "Flickypedia/0.1 (https://commons.wikimedia.org/wiki/Commons:Flickypedia; hello@flickr.org)",
    }


def get_directories(config: dict[str, typing.Any]) -> list[str]:
    """
    A list of directories that need to be created on startup.
    """
    return [
        config["FLICKR_API_RESPONSE_CACHE"],
        config["DUPLICATE_DATABASE_DIRECTORY"],
    ]
