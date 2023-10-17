#!/usr/bin/env python3
"""
Find the Flickr photo URLs in the structured data on files in
Wikimedia Commons.  It creates a spreadsheet like:

    flickr_photo_id,wikimedia_title,wikimedia_page_id
    3176098,File:Crocodile grin-scubadive67.jpg,M63606
    7267164,File:Rfid implant after.jpg,M87190
    9494179,File:Madrid Metro Sign.jpg,M137548

"""

import bz2
import csv
import json
import sys

from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
import tqdm

from flickypedia.apis.wikidata import WikidataEntities, WikidataProperties


def get_structured_data_records(path):
    """
    Given a snapshot of SDC from Wikimedia Commons, generate every entry.
    """
    # The file is returned as a massive JSON object, but we can
    # stream it fairly easily: there's an opening [, then one
    # object per line, i.e.:
    #
    #     [
    #       {…},
    #       {…},
    #       {…}
    #     ]
    #
    # So if we go line-by-line, we can stream the file without having
    # to load it all into memory.
    with bz2.open(path) as in_file:
        for line in in_file:
            if line == b"[\n":
                continue

            yield json.loads(line.replace(b",\n", b""))


def _is_wikibase_entity(v, *, entity_id):
    return (
        v["datavalue"]["type"] == "wikibase-entityid"
        and v["datavalue"]["value"]["id"] == entity_id
    )


def find_flickr_photo_id_in_sdc(sdc_object):
    """
    Given an SDC object from the snapshot, find the Flickr photo ID
    from the 'source of file' property (if present).
    """
    try:
        source_of_file = sdc_object["statements"][WikidataProperties.SourceOfFile][0]

        if not _is_wikibase_entity(
            source_of_file["mainsnak"],
            entity_id=WikidataEntities.FileAvailableOnInternet,
        ):
            return

        if not _is_wikibase_entity(
            source_of_file["qualifiers"][WikidataProperties.Operator][0],
            entity_id=WikidataEntities.Flickr,
        ):
            return

        photo_url = source_of_file["qualifiers"][WikidataProperties.DescribedAtUrl][0][
            "datavalue"
        ]["value"]

        # If we can find a statement for 'source of file' with Flickr
        # as the operator, try to parse it.
        #
        # If we can't parse it, save the URL to a separate file for analysis --
        # this could be a bug in our parsing code, or bad data in WMC.
        try:
            parsed_url = parse_flickr_url(photo_url)
        except (NotAFlickrUrl, UnrecognisedUrl) as err:
            with open("sdc_errors.txt", "a") as out_file:
                out_file.write(
                    json.dumps(
                        {
                            "title": sdc_object["title"],
                            "flickr_url": photo_url,
                            "err": str(err),
                        }
                    )
                    + "\n"
                )

            return

        # We can only deal with single photo URLs here.  Sometimes there
        # are non-photo URLs (e.g. a link to the photographer's profile
        # rather than the individual image) but we can't do much about that.
        if parsed_url["type"] == "single_photo":
            return parsed_url["photo_id"]
        else:
            with open("sdc_warnings.txt", "a") as out_file:
                out_file.write(
                    json.dumps(
                        {
                            "title": sdc_object["title"],
                            "flickr_url": photo_url,
                        }
                    )
                    + "\n"
                )

    except (KeyError, IndexError):
        return


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except IndexError:
        sys.exit(f"Usage: {__file__} <PATH>")

    with open("flickr_ids_from_sdc.csv", "w") as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=["flickr_photo_id", "wikimedia_title", "wikimedia_page_id"],
        )
        writer.writeheader()

        for sdc_object in tqdm.tqdm(get_structured_data_records(path)):
            photo_id = find_flickr_photo_id_in_sdc(sdc_object)
            if photo_id is not None:
                writer.writerow(
                    {
                        "flickr_photo_id": photo_id,
                        "wikimedia_title": sdc_object["title"],
                        "wikimedia_page_id": sdc_object["id"],
                    }
                )
                # print(photo_id)
                # print(repr(line))
                # assert 0
