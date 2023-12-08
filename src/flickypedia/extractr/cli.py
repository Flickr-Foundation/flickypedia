import click
import tqdm

from flickypedia.apis.structured_data import find_flickr_photo_id
from flickypedia.apis.snapshots import parse_sdc_snapshot


@click.group(
    help="Get information about Flickr photos on WMC",
)
def extractr() -> None:
    pass


@extractr.command(help="Get a list of Flickr photos on Commons.")
@click.argument("SNAPSHOT_PATH")
def get_list_of_photos(snapshot_path: str) -> None:
    for entry in tqdm.tqdm(parse_sdc_snapshot(snapshot_path)):
        try:
            flickr_photo_id = find_flickr_photo_id(entry['statements'])
        except Exception:
            import json
            from pprint import pprint; print(json.dumps(entry['statements']))
            raise


        from pprint import pprint; pprint()
        from pprint import pprint; pprint(entry['statements'])
        break

    print(snapshot_path)
