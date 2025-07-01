import json

from click.testing import CliRunner
import keyring
from keyring.backend import KeyringBackend

from nitrate.mock_keyring import *  # noqa: F403

from flickypedia.cli import main as cli_main


def test_store_flickypedia_bot_token(
    mock_keyring: KeyringBackend, flickr_oauth_cassette: str
) -> None:
    """
    This tests the steps of getting and saving a Flickr OAuth 1.0a token
    for the Flickypedia bot account.

    I inspected the VCR cassette for this test quite carefully,
    to ensure I wasn't leaking any real tokens.
    """
    mock_keyring.set_password("flickypedia", "api_key", "12345")
    mock_keyring.set_password("flickypedia", "api_secret", "67890")

    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["uploadr", "store-flickypedia-bot-token"], input="429-793-767\n"
    )

    assert result.exit_code == 0

    stored_token = keyring.get_password("flickypedia.bot", "oauth_token")
    assert stored_token is not None

    assert json.loads(stored_token) == {
        "oauth_token": "FLICKYPEDIA_OAUTH_TOKEN_123",
        "oauth_token_secret": "FLICKYPEDIA_OAUTH_SECRET_456",
        "oauth_verifier": None,
    }


def test_only_stores_a_token_for_flickypedia_bot(
    mock_keyring: KeyringBackend, flickr_oauth_cassette: str
) -> None:
    """
    This tests that we can only store a token for the Flickypedia bot user.

    If we accidentally log as to another user here, it will reject it.

    This test uses a hand-edited copy of the VCR cassette for
    ``test_store_flickypedia_bot_token()``.
    """
    mock_keyring.set_password("flickypedia", "api_key", "12345")
    mock_keyring.set_password("flickypedia", "api_secret", "67890")

    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["uploadr", "store-flickypedia-bot-token"], input="429-793-767\n"
    )

    assert result.exit_code == 1

    assert (
        "This is only meant to be used to fetch credentials for the Flickypedia bot account!"
        in result.output
    )
    assert "You logged in as 'example'!" in result.output
