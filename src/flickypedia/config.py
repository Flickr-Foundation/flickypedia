import os


def create_config(data_directory):
    """
    Create the config for Flickypedia.

    Flickypedia writes a number of temporary files as part of its work.
    The ``data_directory`` is their root.
    """
    celery_directory = os.path.join(data_directory, "celery")

    celery_config = {
        "result_backend": f"file://{celery_directory}/results",
        "broker_url": "filesystem://",
        "broker_transport_options": {
            "data_folder_in": os.path.join(celery_directory, "queue"),
            "data_folder_out": os.path.join(celery_directory, "queue"),
            "processed_folder": os.path.join(celery_directory, "processed"),
            #
            # This isn't a Celery config option, but it's used by
            # Celery in our app for tracking in-progress work.
            #
            # We store it here for convenience.
            "in_progress_folder": os.path.join(celery_directory, "in_progress_folder"),
            #
            # The processed tasks include the original arguments passed
            # to Celery, which has the user's OAuth credentials in
            # plain text, so we don't want to keep them around.
            "store_processed": False,
        },
    }

    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY") or "you-will-never-guess",
        "FLICKR_API_KEY": os.environ.get("FLICKR_API_KEY", "<UNKNOWN>"),
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{os.path.abspath(data_directory)}/db.sqlite",
        #
        # Used as a temporary cache for responses from the Flickr API.
        #
        # We can save results in here, and pass the filename around in the
        # user session.  This is just public data from the Flickr API,
        # so there's nothing sensitive in here.
        "FLICKR_API_RESPONSE_CACHE": os.path.join(data_directory, "flickr_api_cache"),
        #
        # Used as a directory to find SQLite databases which contain information
        # about duplicates.
        "DUPLICATE_DATABASE_DIRECTORY": os.path.join(data_directory, "duplicates"),
        "OAUTH2_PROVIDERS": {
            # Implementation note: although these URLs are currently hard-coded,
            # there is a beta cluster we might use in the future.  It's currently
            # broken, so we're not adding support for it yet, but we could if
            # it ever gets fixed.
            #
            # See https://github.com/Flickr-Foundation/flickypedia/issues/4
            "wikimedia": {
                "client_id": os.environ.get("WIKIMEDIA_CLIENT_ID"),
                "client_secret": os.environ.get("WIKIMEDIA_CLIENT_SECRET"),
                "authorize_url": "https://meta.wikimedia.org/w/rest.php/oauth2/authorize",
                "token_url": "https://meta.wikimedia.org/w/rest.php/oauth2/access_token",
            }
        },
        "CELERY": celery_config,
        #
        # The IDs of licenses that we can upload to Flickypedia.
        "ALLOWED_LICENSES": {"cc-by-2.0", "cc-by-sa-2.0", "usgov", "cc0-1.0", "pdm"},
        #
        # The number of photos to show on a single page
        "PHOTOS_PER_PAGE": 100,
        #
        # A User-Agent sent on HTTP requests
        "USER_AGENT": "Flickypedia/0.1 (https://commons.wikimedia.org/wiki/Commons:Flickypedia; hello@flickr.org)",
    }


def get_directories(config):
    """
    A list of directories that need to be created on startup.
    """
    return [
        config["FLICKR_API_RESPONSE_CACHE"],
        config["DUPLICATE_DATABASE_DIRECTORY"],
        config["CELERY"]["result_backend"].replace("file://", ""),
        config["CELERY"]["broker_transport_options"]["data_folder_in"],
        config["CELERY"]["broker_transport_options"]["data_folder_out"],
        config["CELERY"]["broker_transport_options"]["processed_folder"],
        config["CELERY"]["broker_transport_options"]["in_progress_folder"],
    ]
