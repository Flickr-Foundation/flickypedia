from flickypedia.backfillr.comparisons import are_equivalent_statements
from flickypedia.types.structured_data import ExistingStatement, NewStatement


def test_different_types_are_not_equivalent() -> None:
    existing_statement: ExistingStatement = {
        "id": "M138765382$ECB592B8-1328-427C-880D-E741D631C109",
        "mainsnak": {
            "datavalue": {"type": "string", "value": "53253175319"},
            "hash": "33a66ab2dbc997e9a70e7f73eb6c213d68caa4bf",
            "property": "P12120",
            "snaktype": "value",
        },
        "rank": "normal",
        "type": "statement",
    }

    new_statement: NewStatement = {
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 51.5475,
                    "longitude": -0.261667,
                    "precision": 1e-05,
                },
            },
            "property": "P12120",
            "snaktype": "value",
        },
        "type": "statement",
    }

    assert not are_equivalent_statements(existing_statement, new_statement)


def test_globe_coordinates_differing_only_in_precision_are_equivalent() -> None:
    existing_statement: ExistingStatement = {
        "id": "M227302$30AAFFCE-8A3E-40E2-8001-C2079FE8B18D",
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 51.5475,
                    "longitude": -0.261667,
                    "precision": 1e-06,
                },
            },
            "hash": "801b0e9669ecbd1bb1b5d196d7031c17404b7d71",
            "property": "P1259",
            "snaktype": "value",
        },
        "rank": "normal",
        "type": "statement",
    }

    new_statement: NewStatement = {
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 51.5475,
                    "longitude": -0.261667,
                    "precision": 1e-05,
                },
            },
            "property": "P1259",
            "snaktype": "value",
        },
        "type": "statement",
    }

    assert are_equivalent_statements(existing_statement, new_statement)


def test_globe_coordinates_with_different_values_are_different() -> None:
    existing_statement: ExistingStatement = {
        "id": "M227302$30AAFFCE-8A3E-40E2-8001-C2079FE8B18D",
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 51.5475,
                    "longitude": -0.261667,
                    "precision": 1e-06,
                },
            },
            "hash": "801b0e9669ecbd1bb1b5d196d7031c17404b7d71",
            "property": "P1259",
            "snaktype": "value",
        },
        "rank": "normal",
        "type": "statement",
    }

    new_statement: NewStatement = {
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 12.3987,
                    "longitude": -2.12348,
                    "precision": 1e-05,
                },
            },
            "property": "P1259",
            "snaktype": "value",
        },
        "type": "statement",
    }

    assert not are_equivalent_statements(existing_statement, new_statement)
