import os

from flask_login import FlaskLoginClient
import pytest
import vcr

from flickypedia import create_app
from flickypedia.auth import WikimediaUserSession, SESSION_ID_KEY
from flickypedia.apis.flickr import FlickrApi
from flickypedia.apis.wikimedia import WikimediaApi


@pytest.fixture(scope="function")
def cassette_name(request):
    # By default we use the name of the test as the cassette name,
    # but if it's a test parametrised with @pytest.mark.parametrize,
    # we include the parameter name to distinguish cassettes.
    #
    # See https://stackoverflow.com/a/67056955/1558022 for more info
    # on how this works.
    function_name = request.function.__name__

    try:
        suffix = request.node.callspec.id.replace("https://", "").replace("/", "-")
        return f"{function_name}.{suffix}.yml"
    except AttributeError:
        return f"{function_name}.yml"


@pytest.fixture(scope="function")
def vcr_cassette(cassette_name):
    """
    Creates a VCR cassette for use in tests.

    Anything using httpx in this test will record its HTTP interactions
    as "cassettes" using vcr.py, which can be replayed offline
    (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
    ):
        yield


@pytest.fixture(scope="function")
def wikimedia_api(cassette_name):
    """
    Creates an instance of the WikimediaApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_headers=["authorization"],
    ):
        yield WikimediaApi(
            access_token=os.environ.get("WIKIMEDIA_ACCESS_TOKEN", "<REDACTED>")
        )


@pytest.fixture(scope="function")
def flickr_api(cassette_name):
    """
    Creates an instance of the FlickrApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=["api_key"],
    ):
        yield FlickrApi(
            api_key=os.environ.get("FLICKR_API_KEY", "<REDACTED>"),
            user_agent="Flickypedia/dev (https://commons.wikimedia.org/wiki/Commons:Flickypedia; hello@flickr.org)",
        )


@pytest.fixture()
def app():
    """
    Creates an instance of the app for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    app = create_app()
    app.config["TESTING"] = True

    app.config["DUPLICATE_DATABASE_DIRECTORY"] = "tests/fixtures/duplicates"
    app.config["PHOTOS_PER_PAGE"] = 10

    user_agent = "Flickypedia/dev (https://commons.wikimedia.org/wiki/Commons:Flickypedia; hello@flickr.org)"
    app.config["USER_AGENT"] = user_agent

    # This means I don't need to pass the CSRF token when posting
    # data to forms, which makes things a bit easier.
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    """
    Creates a client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(app):
    """
    Creates a client for use in testing which is logged in.

    See https://flask-login.readthedocs.io/en/latest/#automated-testing
    """
    app.test_client_class = FlaskLoginClient

    user = WikimediaUserSession(
        id=-1,
        userid=-1,
        name="example",
    )

    with app.test_client(user=user) as client:
        with client.session_transaction() as session:
            session[SESSION_ID_KEY] = user.id

        yield client
