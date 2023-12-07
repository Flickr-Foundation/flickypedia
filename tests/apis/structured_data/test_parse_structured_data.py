from flickypedia.apis.structured_data import find_flickr_photo_id
from flickypedia.types.structured_data import ExistingClaims


class TestFindFlickrPhotoId:
    def test_empty_sdc_means_no_flickr_id(self) -> None:
        assert find_flickr_photo_id(sdc={}) is None

    def test_can_find_flickr_id_in_source(self) -> None:
        sdc: ExistingClaims = {
            "P7482": [
                {
                    "id": "M138765382$18DE2E71-EFFC-42CA-B466-83838347748E",
                    "mainsnak": {
                        "datavalue": {
                            "type": "wikibase-entityid",
                            "value": {
                                "entity-type": "item",
                                "id": "Q74228490",
                                "numeric-id": 74228490,
                            },
                        },
                        "hash": "b82dd47222a210c6dc1f428b693c2fbf7b0e0d6e",
                        "property": "P7482",
                        "snaktype": "value",
                    },
                    "qualifiers": {
                        "P137": [
                            {
                                "datavalue": {
                                    "type": "wikibase-entityid",
                                    "value": {
                                        "entity-type": "item",
                                        "id": "Q103204",
                                        "numeric-id": 103204,
                                    },
                                },
                                "hash": "3d8cd4c1ab91d3d9a14900210faaebf1a98b947b",
                                "property": "P137",
                                "snaktype": "value",
                            }
                        ],
                        "P2699": [
                            {
                                "datavalue": {
                                    "type": "string",
                                    "value": "https://live.staticflickr.com/65535/53253175319_2f310021b6_o_d.jpg",
                                },
                                "hash": "4506c651f41a90d58a356c4cb8e131777c328542",
                                "property": "P2699",
                                "snaktype": "value",
                            }
                        ],
                        "P973": [
                            {
                                "datavalue": {
                                    "type": "string",
                                    "value": "https://www.flickr.com/photos/199246608@N02/53253175319/",
                                },
                                "hash": "7f589db379145e6e85c18ac1d2011a0a480e3f02",
                                "property": "P973",
                                "snaktype": "value",
                            }
                        ],
                    },
                    "qualifiers-order": ["P973", "P137", "P2699"],
                    "rank": "normal",
                    "type": "statement",
                }
            ]
        }

        assert find_flickr_photo_id(sdc) == "53253175319"
