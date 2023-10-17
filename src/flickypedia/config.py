import os


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite"

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
            "store_processed": False,
        },
    }
