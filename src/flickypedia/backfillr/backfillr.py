import sys

from flickr_photos_api import FlickrApi, PhotoIsPrivate, ResourceNotFound

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.structured_data import create_sdc_claims_for_existing_flickr_photo
from flickypedia.structured_data.statements import create_flickr_photo_id_statement
from .actions import Action, create_actions
from .flickr_matcher import find_flickr_photo


class Backfillr:
    def __init__(self, *, flickr_api: FlickrApi, wikimedia_api: WikimediaApi):
        self.flickr_api = flickr_api
        self.wikimedia_api = wikimedia_api

    def update_file(self, *, filename: str) -> list[Action]:
        """
        Given a file on Wikimedia Commons, add any extra metadata
        from the current photo on Flickr.
        """
        existing_claims = self.wikimedia_api.get_structured_data(filename=filename)
        flickr_id = find_flickr_photo(
            self.wikimedia_api, existing_sdc=existing_claims, filename=filename
        )

        if flickr_id is None:
            print(f"Unable to find Flickr ID for {filename}", file=sys.stderr)
            raise ValueError(f"Unable to find Flickr ID for {filename}")

        try:
            single_photo = self.flickr_api.get_single_photo(
                photo_id=flickr_id["photo_id"]
            )
            new_claims = create_sdc_claims_for_existing_flickr_photo(single_photo)
            user = single_photo["owner"]
        except (PhotoIsPrivate, ResourceNotFound):
            new_claims = {
                "claims": [
                    create_flickr_photo_id_statement(photo_id=flickr_id["photo_id"])
                ]
            }
            user = None

        actions = create_actions(existing_claims, new_claims, user)

        claims = []

        for a in actions:
            if a["action"] == "unknown" or a["action"] == "do_nothing":
                continue
            elif a["action"] == "add_missing":
                claims.append(a["statement"])
            elif a["action"] == "add_qualifiers" or a["action"] == "replace_statement":
                statement = a["statement"]
                statement["id"] = a["statement_id"]
                claims.append(statement)
            else:  # pragma: no cover
                raise ValueError(f"Unrecognised action: {a['action']}")

        if claims:
            self.wikimedia_api.add_structured_data(
                filename=filename,
                data={"claims": claims},
                summary="Update the [[Commons:Structured data|structured data]] based on metadata from Flickr",
            )

        return actions
