from click.testing import CliRunner

from flickypedia.cli import main as cli_main


def test_it_rejects_a_non_wikimedia_url(vcr_cassette: None) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["backfillr", "update-single-file", "https://example.com"]
    )
    assert result.exit_code == 2

    assert (
        "Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>"
        in result.output
    )
