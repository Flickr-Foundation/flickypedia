import os


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    FLICKR_API_KEY = os.environ.get("FLICKR_API_KEY", "<UNKNOWN>")

    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite"

    # Used as a temporary cache for responses from the Flickr API.
    #
    # We can save results in here, and pass the filename around in the
    # user session.  This is just public data from the Flickr API,
    # so there's nothing sensitive in here.
    FLICKR_API_RESPONSE_CACHE = "flickr_api_cache"

    OAUTH2_PROVIDERS = {
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
    }

    CELERY = {
        "result_backend": "file://tasks/results",
        "broker_url": "filesystem://",
        "broker_transport_options": {
            "data_folder_in": "tasks/queue",
            "data_folder_out": "tasks/queue",
            "processed_folder": "tasks/processed",
            #
            # This isn't a Celery config option, but it's used by
            # Celery in our app for tracking in-progress work.
            #
            # We store it here for convenience.
            "in_progress_folder": "tasks/in_progress_folder",
            #
            # The processed tasks include the original arguments passed
            # to Celery, which has the user's OAuth credentials in
            # plain text, so we don't want to keep them around.
            "store_processed": False,
        },
    }
