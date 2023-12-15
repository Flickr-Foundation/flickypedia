from flickypedia.backfillr.actions import create_actions, has_subset_of_new_qualifiers
from flickypedia.types.structured_data import (
    ExistingClaims,
    ExistingStatement,
    NewClaims,
    NewStatement,
)


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


class TestHasSubsetOfNewQualifiers:
    def test_missing_slash_on_P973_is_fine(self) -> None:
        existing_statement: ExistingStatement = {
            "id": "M63606$D65703C3-1CBF-48A4-B6B4-A2117E764B7F",
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
                            "value": "https://www.flickr.com/photos/71217725@N00/3176098",
                        },
                        "hash": "c2cd7200ace923b7155ea2120ef03629019eaad5",
                        "property": "P973",
                        "snaktype": "value",
                    }
                ],
            },
            "qualifiers-order": ["P137", "P973"],
            "rank": "normal",
            "type": "statement",
        }

        new_statement: NewStatement = {
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
                            "value": "https://live.staticflickr.com/3/3176098_a887b20133_o.jpg",
                        },
                        "property": "P2699",
                        "snaktype": "value",
                    }
                ],
                "P973": [
                    {
                        "datavalue": {
                            "type": "string",
                            "value": "https://www.flickr.com/photos/71217725@N00/3176098/",
                        },
                        "property": "P973",
                        "snaktype": "value",
                    }
                ],
            },
            "qualifiers-order": ["P973", "P137", "P2699"],
            "type": "statement",
        }

        assert has_subset_of_new_qualifiers(existing_statement, new_statement)

    def test_distinct_snaks_are_not_equivalent(self) -> None:
        existing_statement: ExistingStatement = {
            "type": "statement",
            "mainsnak": {
                "property": "P170",
                "snaktype": "somevalue",
                "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
            },
            "qualifiers-order": ["P2093", "P3267", "P2699"],
            "qualifiers": {
                "P2093": [
                    {
                        "property": "P2093",
                        "snaktype": "value",
                        "datavalue": {"type": "string", "value": "gailhampshire"},
                        "hash": "34107f837004c0d4b2df516c3804e0f7b1a84f7a",
                    }
                ],
                "P3267": [
                    {
                        "property": "P3267",
                        "snaktype": "value",
                        "datavalue": {"type": "string", "value": "43272765@N04"},
                        "hash": "ffeb5297cca6e61917a550bf0d851d751a66a6bf",
                    }
                ],
                "P2699": [
                    {
                        "property": "P2699",
                        "snaktype": "value",
                        "datavalue": {
                            "type": "string",
                            "value": "https://www.flickr.com/people/43272765@N04",
                        },
                        "hash": "2fb3055120dabbe2af867f82e9846dd55fbb1a42",
                    }
                ],
            },
            "id": "M49978218$3A484C4A-A1B8-4CD0-A853-F6E0DB7DDF09",
            "rank": "normal",
        }
        new_statement: NewStatement = {
            "mainsnak": {"snaktype": "somevalue", "property": "P170"},
            "qualifiers": {
                "P2093": [
                    {
                        "datavalue": {"value": "gailhampshire", "type": "string"},
                        "property": "P2093",
                        "snaktype": "value",
                    }
                ],
                "P2699": [
                    {
                        "datavalue": {
                            "value": "https://www.flickr.com/people/gails_pictures/",
                            "type": "string",
                        },
                        "property": "P2699",
                        "snaktype": "value",
                    }
                ],
                "P3267": [
                    {
                        "datavalue": {"value": "43272765@N04", "type": "string"},
                        "property": "P3267",
                        "snaktype": "value",
                    }
                ],
            },
            "qualifiers-order": ["P3267", "P2093", "P2699"],
            "type": "statement",
        }

        assert not has_subset_of_new_qualifiers(existing_statement, new_statement)


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

    new_sdc: NewClaims = {"claims": [statement]}

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
        {
            "property_id": "P7482",
            "action": "unknown",
        }
    ]


def test_a_null_creator_statement_is_replaced() -> None:
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
    statement: NewStatement = {
        "mainsnak": {"snaktype": "somevalue", "property": "P170"},
        "qualifiers": {
            "P2093": [
                {
                    "datavalue": {"value": "StrangeInterlude", "type": "string"},
                    "property": "P2093",
                    "snaktype": "value",
                }
            ],
            "P2699": [
                {
                    "datavalue": {
                        "value": "https://www.flickr.com/people/strangeinterlude/",
                        "type": "string",
                    },
                    "property": "P2699",
                    "snaktype": "value",
                }
            ],
            "P3267": [
                {
                    "datavalue": {"value": "44124472424@N01", "type": "string"},
                    "property": "P3267",
                    "snaktype": "value",
                }
            ],
        },
        "qualifiers-order": ["P3267", "P2093", "P2699"],
        "type": "statement",
    }

    existing_sdc: ExistingClaims = {"P170": [existing_statement]}
    new_sdc: NewClaims = {"claims": [statement]}

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
        {
            "property_id": "P170",
            "action": "replace_statement",
            "statement_id": "M26828$E5B1DA53-7604-4B6F-B07A-21BC098CEEC9",
            "statement": statement,
        }
    ]


def test_a_creator_is_replaced_if_numeric_id_in_alias() -> None:
    existing_statement: ExistingStatement = {
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
    new_statement: NewStatement = {
        "mainsnak": {"snaktype": "somevalue", "property": "P170"},
        "qualifiers": {
            "P2093": [
                {
                    "datavalue": {"value": "Jason Pratt", "type": "string"},
                    "property": "P2093",
                    "snaktype": "value",
                }
            ],
            "P2699": [
                {
                    "datavalue": {
                        "value": "https://www.flickr.com/people/jasonpratt/",
                        "type": "string",
                    },
                    "property": "P2699",
                    "snaktype": "value",
                }
            ],
            "P3267": [
                {
                    "datavalue": {"value": "84108876@N00", "type": "string"},
                    "property": "P3267",
                    "snaktype": "value",
                }
            ],
        },
        "qualifiers-order": ["P3267", "P2093", "P2699"],
        "type": "statement",
    }

    existing_sdc: ExistingClaims = {"P170": [existing_statement]}
    new_sdc: NewClaims = {"claims": [new_statement]}

    actions = create_actions(existing_sdc, new_sdc)

    assert actions == [
        {
            "property_id": "P170",
            "action": "replace_statement",
            "statement_id": "M34597$10AA104E-CFBD-44C2-8D43-FF8C48FE428A",
            "statement": new_statement,
        }
    ]
