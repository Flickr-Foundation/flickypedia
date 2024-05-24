from flickr_photos_api import FlickrApi, User as FlickrUser
import pytest

from flickypedia.backfillr.actions import create_actions
from flickypedia.apis.structured_data import create_flickr_creator_statement
from flickypedia.types.structured_data import (
    ExistingClaims,
    ExistingStatement,
    NewClaims,
    NewStatement,
)


null_user: FlickrUser = {
    "id": "-1",
    "path_alias": None,
    "username": "example",
    "realname": None,
    "photos_url": "https://www.flickr.com/photos/-1",
    "profile_url": "https://www.flickr.com/people/-1",
}


def test_missing_statement_is_added() -> None:
    statement: NewStatement = {
        "mainsnak": {
            "datavalue": {"type": "string", "value": "53253175319"},
            "property": "P12120",
            "snaktype": "value",
        },
        "type": "statement",
    }

    existing_sdc: ExistingClaims = {}
    new_sdc: NewClaims = {"claims": [statement]}

    assert create_actions(existing_sdc, new_sdc, user=null_user) == [
        {"property_id": "P12120", "action": "add_missing", "statement": statement}
    ]


def test_equivalent_statement_is_no_op() -> None:
    existing_sdc: ExistingClaims = {
        "P170": [
            {
                "id": "M138765382$505642FD-63FB-4397-8AC5-F48E59DE3142",
                "mainsnak": {
                    "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
                    "property": "P170",
                    "snaktype": "somevalue",
                },
                "qualifiers": {
                    "P2093": [
                        {
                            "datavalue": {"type": "string", "value": "Alex Chan"},
                            "hash": "fab51479c0c03b1a3784816008ab10515b259301",
                            "property": "P2093",
                            "snaktype": "value",
                        }
                    ],
                    "P2699": [
                        {
                            "datavalue": {
                                "type": "string",
                                "value": "https://www.flickr.com/people/199246608@N02/",
                            },
                            "hash": "9bad7272b27927e7b6ea13142cd1800221cb8aa4",
                            "property": "P2699",
                            "snaktype": "value",
                        }
                    ],
                    "P3267": [
                        {
                            "datavalue": {"type": "string", "value": "199246608@N02"},
                            "hash": "720421850357074e74457b9bdc5c93c477a1ab81",
                            "property": "P3267",
                            "snaktype": "value",
                        }
                    ],
                },
                "qualifiers-order": ["P3267", "P2093", "P2699"],
                "rank": "normal",
                "type": "statement",
            }
        ]
    }

    new_sdc: NewClaims = {
        "claims": [
            {
                "mainsnak": {"property": "P170", "snaktype": "somevalue"},
                "qualifiers": {
                    "P2093": [
                        {
                            "datavalue": {"type": "string", "value": "Alex Chan"},
                            "property": "P2093",
                            "snaktype": "value",
                        }
                    ],
                    "P2699": [
                        {
                            "datavalue": {
                                "type": "string",
                                "value": "https://www.flickr.com/people/199246608@N02/",
                            },
                            "property": "P2699",
                            "snaktype": "value",
                        }
                    ],
                    "P3267": [
                        {
                            "datavalue": {"type": "string", "value": "199246608@N02"},
                            "property": "P3267",
                            "snaktype": "value",
                        }
                    ],
                },
                "qualifiers-order": ["P3267", "P2093", "P2699"],
                "type": "statement",
            }
        ]
    }

    assert create_actions(existing_sdc, new_sdc, user=null_user) == [
        {"property_id": "P170", "action": "do_nothing"}
    ]


def test_adds_qualifiers_if_existing_are_subset_of_new() -> None:
    existing_sdc: ExistingClaims = {
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
                    ]
                },
                "qualifiers-order": ["P137"],
                "rank": "normal",
                "type": "statement",
            }
        ]
    }

    statement: NewStatement = {
        "mainsnak": {
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {
                    "entity-type": "item",
                    "id": "Q74228490",
                    "numeric-id": 74228490,
                },
            },
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
                    "property": "P137",
                    "snaktype": "value",
                }
            ],
            "P2699": [
                {
                    "datavalue": {
                        "type": "string",
                        "value": "https://live.staticflickr.com/65535/53253175319_2f310021b6_o.jpg",
                    },
                    "property": "P2699",
                    "snaktype": "value",
                }
            ],
        },
        "qualifiers-order": ["P137", "P2699"],
        "type": "statement",
    }

    new_sdc: NewClaims = {"claims": [statement]}

    assert create_actions(existing_sdc, new_sdc, user=null_user) == [
        {
            "property_id": "P7482",
            "action": "add_qualifiers",
            "statement": statement,
            "statement_id": "M138765382$18DE2E71-EFFC-42CA-B466-83838347748E",
        }
    ]


def test_does_not_qualifiers_if_existing_are_disjoint_from_new() -> None:
    existing_sdc: ExistingClaims = {
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
                "qualifiers-order": ["P137", "P973"],
                "rank": "normal",
                "type": "statement",
            }
        ]
    }

    statement: NewStatement = {
        "mainsnak": {
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {
                    "entity-type": "item",
                    "id": "Q74228490",
                    "numeric-id": 74228490,
                },
            },
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
                    "property": "P137",
                    "snaktype": "value",
                }
            ],
            "P2699": [
                {
                    "datavalue": {
                        "type": "string",
                        "value": "https://live.staticflickr.com/65535/53253175319_2f310021b6_o.jpg",
                    },
                    "property": "P2699",
                    "snaktype": "value",
                }
            ],
        },
        "qualifiers-order": ["P137", "P2699"],
        "type": "statement",
    }

    new_claims: NewClaims = {"claims": [statement]}

    assert create_actions(existing_sdc, new_claims, user=null_user) == [
        {
            "property_id": "P7482",
            "action": "unknown",
        }
    ]


def test_a_null_creator_statement_is_replaced(flickr_api: FlickrApi) -> None:
    existing_statement: ExistingStatement = {
        "type": "statement",
        "mainsnak": {
            "property": "P170",
            "snaktype": "somevalue",
            "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
        },
        "qualifiers-order": ["P2093"],
        "qualifiers": {
            "P2093": [
                {
                    "property": "P2093",
                    "snaktype": "value",
                    "datavalue": {"type": "string", "value": "null"},
                    "hash": "d869bebb956d8c4512616ca1f2ef7907d7ed9705",
                }
            ]
        },
        "id": "M26828$E5B1DA53-7604-4B6F-B07A-21BC098CEEC9",
        "rank": "normal",
    }
    existing_claims: ExistingClaims = {"P170": [existing_statement]}

    user = flickr_api.get_user(user_id="44124472424@N01")
    new_statement = create_flickr_creator_statement(user)
    new_claims: NewClaims = {"claims": [new_statement]}

    assert create_actions(existing_claims, new_claims, user) == [
        {
            "property_id": "P170",
            "action": "replace_statement",
            "statement_id": existing_statement["id"],
            "statement": new_statement,
        }
    ]


def test_it_does_nothing_if_creator_differs_only_in_url(flickr_api: FlickrApi) -> None:
    """
    If the statements are the same, except the URL on WMC uses
    the numeric ID and the URL on Flickr uses the pathalias, we
    can leave the URL on WMC as-is.
    """
    existing_claims: ExistingClaims = {
        "P170": [
            {
                "type": "statement",
                "mainsnak": {
                    "property": "P170",
                    "snaktype": "somevalue",
                    "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
                },
                "qualifiers-order": ["P3267", "P2093", "P2699"],
                "qualifiers": {
                    "P3267": [
                        {
                            "property": "P3267",
                            "snaktype": "value",
                            "datavalue": {"type": "string", "value": "84108876@N00"},
                            "hash": "fa5d6acd35ca6e50077b15e3c224124df6e28595",
                        }
                    ],
                    "P2093": [
                        {
                            "property": "P2093",
                            "snaktype": "value",
                            "datavalue": {"type": "string", "value": "Jason Pratt"},
                            "hash": "5208955c9216bddf416e4c58ce5a13ce1ab8d3fb",
                        }
                    ],
                    "P2699": [
                        {
                            "property": "P2699",
                            "snaktype": "value",
                            "datavalue": {
                                "type": "string",
                                "value": "https://www.flickr.com/people/84108876@N00",
                            },
                            "hash": "0a168876994e47b9028659a4d67e692138556291",
                        }
                    ],
                },
                "id": "M34597$10AA104E-CFBD-44C2-8D43-FF8C48FE428A",
                "rank": "normal",
            }
        ]
    }

    user = flickr_api.get_user(user_id="84108876@N00")
    new_claims: NewClaims = {"claims": [create_flickr_creator_statement(user)]}

    assert create_actions(existing_claims, new_claims, user) == [
        {"property_id": "P170", "action": "do_nothing"}
    ]


def test_it_does_nothing_for_mismatched_creator(flickr_api: FlickrApi) -> None:
    """
    This is a regression test based on the following file:
    https://commons.wikimedia.org/wiki/File:Neasden_Temple_-_Shree_Swaminarayan_Hindu_Mandir_-_Power_Plant.jpg

    The existing P170 statement has a Wikidata entity, which we don't
    know how to handle, so we should do nothing.
    """
    existing_claims: ExistingClaims = {
        "P170": [
            {
                "type": "statement",
                "mainsnak": {
                    "property": "P170",
                    "snaktype": "value",
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {
                            "entity-type": "item",
                            "id": "Q5006102",
                            "numeric-id": 5006102,
                        },
                    },
                    "hash": "f83b12bd22b4f4bec06e037dd57b559aa735fae7",
                },
                "id": "M227302$155FEB72-8819-4DCD-ACF6-AD5D5A1ED3A6",
                "rank": "normal",
            }
        ],
    }

    user = flickr_api.get_user(user_id="52890443@N02")
    new_claims: NewClaims = {"claims": [create_flickr_creator_statement(user)]}

    assert create_actions(existing_claims, new_claims, user) == [
        {"action": "unknown", "property_id": "P170"}
    ]


def test_it_ignores_extra_roles_in_creator_if_otherwise_equivalent(
    flickr_api: FlickrApi,
) -> None:
    # Based on https://commons.wikimedia.org/wiki/File:Programme_(1919)_(14783412743).jpg
    # Retrieved 9 May 2024
    existing_claims: ExistingClaims = {
        "P170": [
            {
                "type": "statement",
                "mainsnak": {
                    "property": "P170",
                    "snaktype": "somevalue",
                    "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
                },
                "qualifiers-order": ["P3831", "P2093", "P3267", "P2699"],
                "qualifiers": {
                    "P3831": [
                        {
                            "property": "P3831",
                            "snaktype": "value",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {
                                    "entity-type": "item",
                                    "id": "Q33231",
                                    "numeric-id": 33231,
                                },
                            },
                            "hash": "c5e04952fd00011abf931be1b701f93d9e6fa5d7",
                        }
                    ],
                    "P2093": [
                        {
                            "property": "P2093",
                            "snaktype": "value",
                            "datavalue": {
                                "type": "string",
                                "value": "Internet Archive Book Images",
                            },
                            "hash": "407646c600d296f66b9b08acf1e09bd36814c83d",
                        }
                    ],
                    "P3267": [
                        {
                            "property": "P3267",
                            "snaktype": "value",
                            "datavalue": {"type": "string", "value": "126377022@N07"},
                            "hash": "19d030d2329f5e7b395a6e0a2df538053fa4ec11",
                        }
                    ],
                    "P2699": [
                        {
                            "property": "P2699",
                            "snaktype": "value",
                            "datavalue": {
                                "type": "string",
                                "value": "https://www.flickr.com/people/126377022@N07",
                            },
                            "hash": "4d79b9f1f095fec5270b5c5ee9f549602270135d",
                        }
                    ],
                },
                "id": "M43417962$70B1AA68-B675-4EBA-8A1E-A3F5F1243944",
                "rank": "normal",
            }
        ],
    }

    user = flickr_api.get_user(user_id="126377022@N07")
    new_claims: NewClaims = {"claims": [create_flickr_creator_statement(user)]}

    assert create_actions(existing_claims, new_claims, user) == [
        {"property_id": "P170", "action": "do_nothing"}
    ]


@pytest.mark.parametrize(
    "author_name",
    ["flickr user Bryce Edwards", "Flickr user Bryce Edwards", "Bryce Edwards"],
)
def test_it_replaces_an_author_name(flickr_api: FlickrApi, author_name: str) -> None:
    existing_statement: ExistingStatement = {
        "type": "statement",
        "mainsnak": {
            "property": "P170",
            "snaktype": "somevalue",
            "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
        },
        "qualifiers-order": ["P2093"],
        "qualifiers": {
            "P2093": [
                {
                    "property": "P2093",
                    "snaktype": "value",
                    "datavalue": {
                        "type": "string",
                        "value": author_name,
                    },
                    "hash": "a193269ae888171ae46da83b8fb92dbbce2497c7",
                }
            ]
        },
        "id": "M1899107$D9951FC5-A183-43EF-85D6-6E8DFCD6DC34",
        "rank": "normal",
    }
    existing_claims: ExistingClaims = {"P170": [existing_statement]}

    user = flickr_api.get_user(user_id="40286210@N00")
    new_statement = create_flickr_creator_statement(user)
    new_claims: NewClaims = {"claims": [new_statement]}

    assert create_actions(existing_claims, new_claims, user) == [
        {
            "property_id": "P170",
            "action": "replace_statement",
            "statement_id": existing_statement["id"],
            "statement": new_statement,
        }
    ]


@pytest.mark.parametrize(
    "author_name",
    ["flickr user Not Bryce Edwards", "fl user Bryce Edwards", "Bruce Edward"],
)
def test_it_skips_an_unrecognised_author_name(
    flickr_api: FlickrApi, author_name: str
) -> None:
    existing_claims: ExistingClaims = {
        "P170": [
            {
                "type": "statement",
                "mainsnak": {
                    "property": "P170",
                    "snaktype": "somevalue",
                    "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
                },
                "qualifiers-order": ["P2093"],
                "qualifiers": {
                    "P2093": [
                        {
                            "property": "P2093",
                            "snaktype": "value",
                            "datavalue": {
                                "type": "string",
                                "value": author_name,
                            },
                            "hash": "a193269ae888171ae46da83b8fb92dbbce2497c7",
                        }
                    ]
                },
                "id": "M1899107$D9951FC5-A183-43EF-85D6-6E8DFCD6DC34",
                "rank": "normal",
            }
        ],
    }

    user = flickr_api.get_user(user_id="40286210@N00")
    new_statement = create_flickr_creator_statement(user)
    new_claims: NewClaims = {"claims": [new_statement]}

    assert create_actions(existing_claims, new_claims, user) == [
        {
            "property_id": "P170",
            "action": "unknown",
        }
    ]


def test_it_replaces_an_author_pathalias(flickr_api: FlickrApi) -> None:
    existing_statement: ExistingStatement = {
        "type": "statement",
        "mainsnak": {
            "property": "P170",
            "snaktype": "somevalue",
            "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
        },
        "qualifiers-order": ["P2093"],
        "qualifiers": {
            "P2093": [
                {
                    "property": "P2093",
                    "snaktype": "value",
                    "datavalue": {"type": "string", "value": "dwhartwig"},
                    "hash": "a0c63c1fe81dff8f300427326a19939afb65ad95",
                }
            ]
        },
        "id": "M108119123$1B7C1641-4F9A-4B73-B059-190083E2AC9F",
        "rank": "normal",
    }

    existing_claims: ExistingClaims = {"P170": [existing_statement]}

    user = flickr_api.get_user(user_id="9751269@N07")
    new_statement = create_flickr_creator_statement(user)
    new_claims: NewClaims = {"claims": [new_statement]}

    assert create_actions(existing_claims, new_claims, user) == [
        {
            "property_id": "P170",
            "action": "replace_statement",
            "statement_id": existing_statement["id"],
            "statement": new_statement,
        }
    ]
