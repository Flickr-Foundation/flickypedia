from collections.abc import Iterator
import os
import pathlib
import shutil

from flask import Flask
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient, current_user
from flickr_photos_api import FlickrApi
import httpx
import pytest
from pytest import FixtureRequest
import vcr

from flickypedia.uploadr import create_app
from flickypedia.uploadr.auth import SESSION_ENCRYPTION_KEY
from flickypedia.apis import WikimediaApi
from utils import store_user


@pytest.fixture
def user_agent() -> str:
    return "Flickypedia/dev (https://commons.wikimedia.org/wiki/Commons:Flickypedia; hello@flickr.org)"


@pytest.fixture(scope="function")
def cassette_name(request: FixtureRequest) -> str:
    """
    Returns the name of a cassette for vcr.py.

    The name can be made up of (up to) three parts:

    -   the name of the test class
    -   the name of the test function
    -   the ID of the test case in @pytest.mark.parametrize

    """
    if request.cls is not None:
        return f"{request.cls.__name__}.{request.node.name}.yml"
    else:
        return f"{request.node.name}.yml"


@pytest.fixture(scope="function")
def vcr_cassette(cassette_name: str) -> Iterator[None]:
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
def wikimedia_api(cassette_name: str) -> Iterator[WikimediaApi]:
    """
    Creates an instance of the WikimediaApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).

    To create VCR cassettes for new tests:

    1.  Create a new Personal API token for Wikimedia, following the
        instructions at:
        https://api.wikimedia.org/wiki/Authentication#Personal_API_tokens
    2.  Put this token in the WIKIMEDIA_PERSONAL_API_TOKEN env var.
    3.  Run the test.
    4.  Check in your new VCR cassette.

    Note that not all Wikimedia APIs require authentication, e.g. the
    category lookup, so you may be able to create VCR cassettes for
    some tests without an API token.
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_headers=["authorization"],
    ):
        # Coverage note: depending on whether you have an API token or
        # not, only one of these branches were run.
        try:  # pragma: no cover
            token = os.environ["WIKIMEDIA_PERSONAL_API_TOKEN"]
            client = httpx.Client(headers={"Authorization": f"Bearer {token}"})
        except KeyError:  # pragma: no cover
            client = httpx.Client()

        yield WikimediaApi(client=client)


@pytest.fixture(scope="function")
def flickr_api(cassette_name: str, user_agent: str) -> Iterator[FlickrApi]:
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
        yield FlickrApi.with_api_key(
            api_key=os.environ.get("FLICKR_API_KEY", "<REDACTED>"),
            user_agent=user_agent,
        )


@pytest.fixture(scope="function")
def flickr_oauth_cassette(cassette_name: str) -> Iterator[str]:
    """
    Creates an instance of the FlickrApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=[
            "oauth_nonce",
            "oauth_signature",
            "oauth_signature_method",
            "oauth_timestamp",
            "oauth_verifier",
        ],
    ):
        yield cassette_name


@pytest.fixture()
def app(user_agent: str, tmp_path: pathlib.Path) -> Iterator[Flask]:
    """
    Creates an instance of the app for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    app = create_app(data_directory=tmp_path)
    app.config["TESTING"] = True

    app.config["DUPLICATE_DATABASE_DIRECTORY"] = os.path.join(tmp_path, "duplicates")
    shutil.copyfile(
        "tests/fixtures/duplicates/flickr_ids_from_sdc_for_testing.sqlite",
        os.path.join(
            app.config["DUPLICATE_DATABASE_DIRECTORY"],
            "flickr_ids_from_sdc_for_testing.sqlite",
        ),
    )

    app.config["PHOTOS_PER_PAGE"] = 10

    app.config["USER_AGENT"] = user_agent

    # This means I don't need to pass the CSRF token when posting
    # data to forms, which makes things a bit easier.
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        yield app


@pytest.fixture()
def client(app: Flask) -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(app: Flask) -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing which is logged in.

    See https://flask-login.readthedocs.io/en/latest/#automated-testing
    """
    app.test_client_class = FlaskLoginClient

    # Note: we have to enter the request context before we enter
    # the test client context.  This took me a while to figure
    # out; see https://stackoverflow.com/a/69961887/1558022
    with app.test_request_context():
        with app.test_client() as client:
            user = store_user(client)

            with client.session_transaction() as session:
                assert SESSION_ENCRYPTION_KEY in session

            assert current_user == user

            yield client


@pytest.fixture
def queue_dir(app: Flask) -> None:
    """
    Creates a queue directory which is pre-populated with some task files.
    """
    shutil.copytree(
        src="tests/fixtures/upload_queue",
        dst=app.config["UPLOAD_QUEUE_DIRECTORY"],
        dirs_exist_ok=True,
    )

    return None
