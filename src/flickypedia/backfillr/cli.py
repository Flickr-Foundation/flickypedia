import click

from flickypedia.apis.wikimedia import get_filename_from_url


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos which have already been uploaded to Wikimedia Commons.",
)
def backfillr() -> None:
    pass


@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    try:
        filename = get_filename_from_url(url)
    except ValueError:
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    print(f"The filename is {filename!r}")
