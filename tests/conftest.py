import os

import pytest
import vcr

from flickypedia import create_app
from flickypedia.apis.wikimedia import WikimediaApi


@pytest.fixture(scope="function")
def cassette_name(request):
    # By default we use the name of the test as the cassette name,
    # but if it's a test parametrised with @pytest.mark.parametrize,
    # we include the parameter name to distinguish cassettes.
    #
    # See https://stackoverflow.com/a/67056955/1558022 for more info
    # on how this works.
    try:
        return f"{request.function.__name__}.{request.node.callspec.id}.yml"
    except AttributeError:
        return f"{request.function.__name__}.yml"


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


@pytest.fixture()
def app():
    """
    Creates an instance of the app for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    app = create_app()
    app.config["TESTING"] = True

    yield app


@pytest.fixture()
def client(app):
    """
    Creates a test client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    return app.test_client()
