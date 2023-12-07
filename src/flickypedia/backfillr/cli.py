import click


@click.group(short_help="Improve SDC for existing Flickr photos", help="Improve the structured data for Flickr photos on Commons.")
def backfillr() -> None:
    pass



@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url) -> None:
    print(url)