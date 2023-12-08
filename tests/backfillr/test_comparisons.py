import pytest

from flickypedia.backfillr.comparisons import (
    are_equivalent_snaks,
    are_equivalent_statements,
)
from flickypedia.types.structured_data import (
    DataValueTypes,
    ExistingStatement,
    NewStatement,
    Snak,
    Value,
)


class TestAreEquivalentSnaks:
    def test_a_snak_is_equivalent_to_itself(self) -> None:
        snak: Snak = {
            "datavalue": {"type": "string", "value": "53253175319"},
            "hash": "33a66ab2dbc997e9a70e7f73eb6c213d68caa4bf",
            "property": "P12120",
            "snaktype": "value",
        }

        assert are_equivalent_snaks(snak, snak)

    def test_snaks_for_different_properties_are_not_equivalent(self) -> None:
        datavalue: DataValueTypes.String = {"type": "string", "value": "ABC"}

        # fmt: off
        snak123: Snak = {"property": "P123", "datavalue": datavalue, "snaktype": "value"}
        snak456: Snak = {"property": "P456", "datavalue": datavalue, "snaktype": "value"}
        # fmt: on

        assert not are_equivalent_snaks(snak123, snak456)

    def test_snaks_with_different_snaktypes_are_not_equivalent(self) -> None:
        datavalue: DataValueTypes.String = {"type": "string", "value": "ABC"}

        # fmt: off
        snak1: Snak = {"snaktype": "value", "property": "P1", "datavalue": datavalue}
        snak2: Snak = {"snaktype": "somevalue", "property": "P1", "datavalue": datavalue}
        # fmt: on

        assert not are_equivalent_snaks(snak1, snak2)

    def test_snaks_with_different_datavalues_types_are_different(self) -> None:
        snak1: Snak = {
            "snaktype": "value",
            "property": "P1",
            "datavalue": {"type": "string", "value": "ABC"},
        }

        snak2: Snak = {
            "snaktype": "value",
            "property": "P1",
            "datavalue": {
                "value": {
                    "id": "Q74228490",
                    "numeric-id": 74228490,
                    "entity-type": "item",
                },
                "type": "wikibase-entityid",
            },
        }

        assert not are_equivalent_snaks(snak1, snak2)

    def test_globecoordinates_which_vary_only_in_precision_are_equivalent(self) -> None:
        value_1e05: Value.GlobeCoordinate = {
            "altitude": None,
            "globe": "http://www.wikidata.org/entity/Q2",
            "latitude": 51.5475,
            "longitude": -0.261667,
            "precision": 1e-05,
        }

        value_1e06: Value.GlobeCoordinate = {
            "altitude": None,
            "globe": "http://www.wikidata.org/entity/Q2",
            "latitude": 51.5475,
            "longitude": -0.261667,
            "precision": 1e-06,
        }

        snak_1e05: Snak = {
            "datavalue": {"type": "globecoordinate", "value": value_1e05},
            "property": "P12120",
            "snaktype": "value",
        }

        snak_1e06: Snak = {
            "datavalue": {"type": "globecoordinate", "value": value_1e06},
            "property": "P12120",
            "snaktype": "value",
        }

        assert are_equivalent_snaks(snak_1e05, snak_1e06)

    @pytest.mark.parametrize(
        "other_value",
        [
            pytest.param(
                {
                    "altitude": 123,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 123,
                    "longitude": 456,
                    "precision": 1e-05,
                },
                id="different_altitude",
            ),
            pytest.param(
                {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q1",
                    "latitude": 123,
                    "longitude": 456,
                    "precision": 1e-05,
                },
                id="different_globe",
            ),
            pytest.param(
                {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": -123,
                    "longitude": 456,
                    "precision": 1e-05,
                },
                id="different_latitude",
            ),
            pytest.param(
                {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": 123,
                    "longitude": -456,
                    "precision": 1e-05,
                },
                id="different_longitude",
            ),
        ],
    )
    def test_different_globecoordinates_are_not_equivalent(
        self, other_value: Value.GlobeCoordinate
    ) -> None:
        this_value: Value.GlobeCoordinate = {
            "altitude": None,
            "globe": "http://www.wikidata.org/entity/Q2",
            "latitude": 123,
            "longitude": 456,
            "precision": 1e-05,
        }

        this_snak: Snak = {
            "datavalue": {"type": "globecoordinate", "value": this_value},
            "property": "P12120",
            "snaktype": "value",
        }

        other_snak: Snak = {
            "datavalue": {"type": "globecoordinate", "value": other_value},
            "property": "P12120",
            "snaktype": "value",
        }

        assert not are_equivalent_snaks(this_snak, other_snak)

    def test_snaks_with_different_values_are_not_equivalent(self) -> None:
        datavalue1: DataValueTypes.String = {"type": "string", "value": "11111"}
        datavalue2: DataValueTypes.String = {"type": "string", "value": "22222"}

        # fmt: off
        snak1: Snak = {"datavalue": datavalue1, "snaktype": "value", "property": "P1"}
        snak2: Snak = {"datavalue": datavalue2, "snaktype": "value", "property": "P1"}
        # fmt: on

        assert not are_equivalent_snaks(snak1, snak2)


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
