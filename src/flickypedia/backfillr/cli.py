import sys

import click
import httpx
import keyring
import termcolor

from flickypedia.apis.flickr import FlickrPhotosApi, ResourceNotFound
from flickypedia.apis.structured_data import (
    create_sdc_claims_for_existing_flickr_photo,
    find_flickr_photo_id,
    find_flickr_urls,
    create_flickr_creator_statement,
    create_flickr_photo_id_statement,
    create_source_data_for_photo,
)
from flickypedia.apis.wikimedia import WikimediaApi, get_filename_from_url
from .actions import create_actions
from .flickr_matcher import find_flickr_photo_id_from_wikitext


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos which have already been uploaded to Wikimedia Commons.",
)
def backfillr() -> None:
    pass


def run_with(list_of_filenames: list[str]):
    api_token = keyring.get_password("flickypedia_backfillr_bot", "api_token")

    wikimedia_api = WikimediaApi(
        client=httpx.Client(headers={"Authorization": f"Bearer {api_token}"})
    )

    flickr_api = FlickrPhotosApi(
        api_key=keyring.get_password("flickr_api", "key"),
        user_agent="Flickypedia Backfillr <hello@flickr.org>",
    )

    for filename in list_of_filenames:
        print("")
        print(filename)

        existing_sdc = wikimedia_api.get_structured_data(filename=filename)

        photo_id = find_flickr_photo_id(existing_sdc)

        if photo_id is None:
            photo_id = find_flickr_photo_id_from_wikitext(
                wikimedia_api, flickr_api, filename=f"File:{filename}"
            )

        if photo_id is None:
            print("Could not find a Flickr photo ID in the existing SDC!")
            continue

        print(f"Found the Flickr photo ID {photo_id}")

        try:
            photo = flickr_api.get_single_photo(photo_id=photo_id)

            new_sdc = create_sdc_claims_for_existing_flickr_photo(photo)
        except ResourceNotFound as e:
            urls = [
                u
                for u, parsed_url in find_flickr_urls(existing_sdc)
                if parsed_url["type"] == "single_photo"
            ]

            if len(urls) == 1 and urls[0].startswith("https://www.flickr.com/photos/"):
                prefix_len = len("https://www.flickr.com/photos/")
                user_url = (
                    "https://www.flickr.com/photos/"
                    + urls[0][prefix_len:].split("/")[0]
                    + "/"
                )

                try:
                    creator = {
                        "https://www.flickr.com/photos/sejmrp/": {
                            "id": "141152160@N02",
                            "username": "Kancelaria Sejmu",
                            "realname": "Sejm RP",
                            "photos_url": "https://www.flickr.com/photos/sejmrp/",
                            "profile_url": "https://www.flickr.com/people/sejmrp/",
                            "path_alias": "sejmrp",
                        },
                        "https://www.flickr.com/photos/usaidafghanistan/": {
                            "id": "49045206@N03",
                            "username": "USAID Afghanistan",
                            "realname": None,
                            "path_alias": "usaidafghanistan",
                            "photos_url": "https://www.flickr.com/photos/usaidafghanistan/",
                            "profile_url": "https://www.flickr.com/people/usaidafghanistan/",
                        },
                        'https://www.flickr.com/photos/paukrus/': {
                            'id': '26244825@N05',
                            'username': 'paukrus',
                            'realname': None,
                            'path_alias': 'paukrus',
                            'photos_url': 'https://www.flickr.com/photos/paukrus/',
                            'profile_url': 'https://www.flickr.com/people/paukrus/',
                        }
                    }[user_url]
                except KeyError:
                    raise

                photo_url = f'https://www.flickr.com/photos/{creator["path_alias"] or creator["id"]}/{photo_id}/'

                new_sdc = {
                    "claims": [
                        create_flickr_photo_id_statement(photo_id=photo_id),
                        create_flickr_creator_statement(user=creator),
                        create_source_data_for_photo(
                            photo_id=photo_id,
                            photo_url=photo_url,
                            original_url=None,
                            retrieved_at=None,
                        ),
                    ]
                }
            else:
                raise

        actions = create_actions(existing_sdc, new_sdc)

        claims = []
        affected_properties = []

        for a in actions:
            if a["action"] == "unknown":
                print(a["property_id"], "\t", termcolor.colored(a["action"], "red"))
            else:
                print(a["property_id"], "\t", a["action"])

            if a["action"] == "add_missing":
                affected_properties.append(a["property_id"])
                claims.append(a["statement"])
            elif a["action"] == "add_qualifiers":
                claims.append({"id": a["statement_id"], **a["statement"]})
                affected_properties.append(a["property_id"])

        if claims:
            wikimedia_api.add_structured_data(
                filename=filename,
                data={"claims": claims},
                summary=f'Update the {", ".join(sorted(affected_properties))} properties in the [[Commons:Structured data|structured data]] based on metadata from Flickr',
            )




@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    try:
        filename = get_filename_from_url(url)
    except ValueError:
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    run_with(list_of_filenames=[filename])


@backfillr.command(help="Fix the SDC for multiple files.")
@click.argument("N")
def update_multiple_files(n: int) -> None:
    seen_titles = set(line.strip() for line in open('seen_titles.txt'))

    i = 0

    import json

    new_titles = []

    for line in open('commonswiki-20231001-flickr_urls3.json'):
        data = json.loads(line)

        if data['title'] in seen_titles:
            continue
        else:
            new_titles.append(data['title'])
            i += 1

        if i >= int(n):
            break

    print(new_titles)
    run_with(list_of_filenames=new_titles)

    for t in new_titles:
        with open('seen_titles.txt', 'a') as outfile:
            outfile.write(t + '\n')
