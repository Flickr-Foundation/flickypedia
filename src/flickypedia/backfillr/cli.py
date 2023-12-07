import click


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos on Commons.",
)
def backfillr() -> None:
    pass


@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    if not url.startswith("https://commons.wikimedia.org/wiki/File:"):
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    filename = url.replace("https://commons.wikimedia.org/wiki/File:", "")
    print(f"Detected filename as {filename!r}")
