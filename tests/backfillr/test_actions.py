from flickypedia.backfillr.actions import create_actions
from flickypedia.types.structured_data import ExistingClaims, NewClaims, NewStatement


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

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
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

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [{"property_id": "P170", "action": "do_nothing"}]


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

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
        {
            "property_id": "P7482",
            "action": "add_qualifiers",
            "statement": statement,
            "statement_id": "M138765382$18DE2E71-EFFC-42CA-B466-83838347748E",
        }
    ]


def test_test_does_not_qualifiers_if_existing_are_disjoint_from_new() -> None:
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

    new_sdc: NewClaims = {"claims": [statement]}

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
        {
            "property_id": "P7482",
            "action": "unknown",
        }
    ]
