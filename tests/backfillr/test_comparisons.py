import pytest

from flickypedia.backfillr.comparisons import (
    are_equivalent_times,
    are_equivalent_flickr_urls,
    are_equivalent_qualifiers,
    are_equivalent_snaks,
    are_equivalent_statements,
)
from flickypedia.types.structured_data import (
    DataValueTypes,
    ExistingStatement,
    NewStatement,
    Qualifiers,
    Snak,
    Value,
)


def create_string_snak(property_id: str, value: str) -> Snak:
    return {
        "datavalue": {
            "type": "string",
            "value": value,
        },
        "hash": "1234567890",
        "property": property_id,
        "snaktype": "value",
    }


class TestAreEquivalentTimes:
    def create_value(self, precision: int, time_str: str) -> Value.Time:
        return {
            "time": time_str,
            "precision": precision,
            "timezone": 0,
            "before": 0,
            "after": 0,
            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
        }

    @pytest.mark.parametrize("precision", [11, 10, 9])
    @pytest.mark.parametrize(
        "time_str",
        [
            "+2012-02-03T12:34:56Z",
            "+1896-01-00T00:00:00Z",
        ],
    )
    def test_time_is_equivalent_to_itself(self, precision: int, time_str: str) -> None:
        assert are_equivalent_times(
            time1=self.create_value(precision, time_str),
            time2=self.create_value(precision, time_str),
        )

    @pytest.mark.parametrize(
        ["precision", "time_str1", "time_str2"],
        [
            # Year-level precision
            (9, "+2001-01-01T01:01:01Z", "+2001-01-01T02:02:02Z"),
            (9, "+2001-01-01T01:01:01Z", "+2001-02-02T02:02:02Z"),
            # Month-level precision
            (10, "+2001-01-01T01:01:01Z", "+2001-01-01T02:02:02Z"),
            (10, "+2001-01-01T01:01:01Z", "+2001-01-02T02:02:02Z"),
            # Day-level precision
            (11, "+2001-01-01T01:01:01Z", "+2001-01-01T02:02:02Z"),
            (11, "+2001-01-01T01:01:01Z", "+2001-01-01T03:04:02Z"),
        ],
    )
    def test_times_are_equivalent_up_to_precision(
        self, precision: int, time_str1: str, time_str2: str
    ) -> None:
        assert are_equivalent_times(
            time1=self.create_value(precision=precision, time_str=time_str1),
            time2=self.create_value(precision=precision, time_str=time_str2),
        )

    @pytest.mark.parametrize(
        ["precision", "time_str1", "time_str2"],
        [
            # Two completely different times
            (9, "+2012-02-03T12:34:56Z", "+2065-12-25T23:45:34Z"),
            # Same in everything but year, year precision
            (9, "+2001-01-01T01:01:01Z", "+2099-01-01T01:01:01Z"),
            # Month precision, different in just year/just month/both
            (10, "+2002-01-01T01:01:01Z", "+2001-01-01T02:02:02Z"),
            (10, "+2001-01-01T01:01:01Z", "+2001-02-01T02:02:02Z"),
            (10, "+2002-01-01T01:01:01Z", "+2001-02-01T02:02:02Z"),
            # Day precision
            (11, "+2001-01-01T01:01:01Z", "+2002-01-01T01:01:01Z"),
            (11, "+2001-01-01T01:01:01Z", "+2001-02-01T01:01:01Z"),
            (11, "+2001-01-01T01:01:01Z", "+2001-01-02T01:01:01Z"),
            # Weird value in one of the fields
            (9, "nope", "+2001-01-01T01:01:01Z"),
            (9, "+2001-01-01T01:01:01Z", "nope"),
        ],
    )
    def test_different_times_are_different(
        self, precision: int, time_str1: str, time_str2: str
    ) -> None:
        assert not are_equivalent_times(
            time1=self.create_value(precision=precision, time_str=time_str1),
            time2=self.create_value(precision=precision, time_str=time_str2),
        )

    @pytest.mark.parametrize("int_field", ["precision", "before", "after", "timezone"])
    def test_differing_in_a_single_property_means_different(
        self, int_field: str
    ) -> None:
        time_str = "+2012-02-03T12:34:56Z"

        time1 = self.create_value(precision=9, time_str=time_str)
        time2 = self.create_value(precision=9, time_str=time_str)

        time2[int_field] += 1  # type: ignore

        assert not are_equivalent_times(time1, time2)

    def test_different_in_calendarmodel_means_different(self) -> None:
        time_str = "+2012-02-03T12:34:56Z"

        time1 = self.create_value(precision=9, time_str=time_str)
        time2 = self.create_value(precision=9, time_str=time_str)

        time2["calendarmodel"] = "http://www.wikidata.org/entity/Q0"

        assert not are_equivalent_times(time1, time2)


class TestAreEquivalentSnaks:
    def test_a_snak_is_equivalent_to_itself(self) -> None:
        snak: Snak = {
            "datavalue": {"type": "string", "value": "53253175319"},
            "hash": "33a66ab2dbc997e9a70e7f73eb6c213d68caa4bf",
            "property": "P12120",
            "snaktype": "value",
        }

        assert are_equivalent_snaks(snak, snak)

    def test_two_samevalue_snaks_are_equivalent(self) -> None:
        existing_snak: Snak = {
            "hash": "d3550e860f988c6675fff913440993f58f5c40c5",
            "property": "P170",
            "snaktype": "somevalue",
        }
        new_snak: Snak = {"property": "P170", "snaktype": "somevalue"}

        assert are_equivalent_snaks(existing_snak, new_snak)

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
        snak1 = create_string_snak(property_id="P1", value="11111")
        snak2 = create_string_snak(property_id="P1", value="22222")

        assert not are_equivalent_snaks(snak1, snak2)

    @pytest.mark.parametrize("property_id", ["P973", "P2699"])
    def test_properties_allow_equivalent_flickr_urls(self, property_id: str) -> None:
        snak_with_numeric_id = create_string_snak(
            property_id=property_id,
            value="https://www.flickr.com/photos/29904699@N00/16100150",
        )

        snak_with_path_alias = create_string_snak(
            property_id=property_id,
            value="https://www.flickr.com/photos/eiriknewth/16100150/",
        )

        assert are_equivalent_snaks(snak_with_numeric_id, snak_with_path_alias)

    @pytest.mark.parametrize("property_id", ["P973", "P2699"])
    def test_properties_block_different_flickr_urls(self, property_id: str) -> None:
        snak1 = create_string_snak(
            property_id=property_id,
            value="https://www.flickr.com/photos/29904699@N00/16100150",
        )

        snak2 = create_string_snak(
            property_id=property_id,
            value="https://www.flickr.com/photos/eiriknewth/",
        )

        assert not are_equivalent_snaks(snak1, snak2)

    def test_times_which_are_same_up_to_precision_are_equivalent(self) -> None:
        # This is based on an existing Commons file:
        # https://commons.wikimedia.org/wiki/File:%22Ada,_31_years._Jan_1896%22_Brockton,_Mass._-_Minette_size%3F_(5458241141).jpg
        # Retrieved 14 December 2023
        existing_snak: Snak = {
            "datavalue": {
                "type": "time",
                "value": {
                    "after": 0,
                    "before": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                    "precision": 10,
                    "time": "+1896-01-01T00:00:00Z",
                    "timezone": 0,
                },
            },
            "hash": "ac360f594d8e5eb8fdbda877255349094ac83592",
            "property": "P571",
            "snaktype": "value",
        }

        new_snak: Snak = {
            "datavalue": {
                "type": "time",
                "value": {
                    "after": 0,
                    "before": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                    "precision": 10,
                    "time": "+1896-01-00T00:00:00Z",
                    "timezone": 0,
                },
            },
            "property": "P571",
            "snaktype": "value",
        }

        assert are_equivalent_snaks(existing_snak, new_snak)


class TestAreEquivalentQualifiers:
    @pytest.mark.parametrize(
        "existing_qualifiers",
        [{}, {"P123": [create_string_snak(property_id="P123", value="Hello world")]}],
    )
    def test_empty_qualifiers_are_equivalent(
        self, existing_qualifiers: Qualifiers
    ) -> None:
        assert are_equivalent_qualifiers(existing_qualifiers, new_qualifiers={})

    def test_qualifiers_with_matching_snaks_are_equivalent(self) -> None:
        existing_qualifiers = {
            "P123": [
                create_string_snak(property_id="P123", value="hello world"),
                create_string_snak(property_id="P123", value="bonjour monde"),
            ],
            "P456": [create_string_snak(property_id="P456", value="jane smith")],
        }

        new_qualifiers = {
            "P123": [create_string_snak(property_id="P123", value="hello world")]
        }

        assert are_equivalent_qualifiers(existing_qualifiers, new_qualifiers)

    def test_qualifiers_with_different_snaks_are_not_equivalent(self) -> None:
        existing_qualifiers = {
            "P123": [
                create_string_snak(property_id="P123", value="hello world"),
                create_string_snak(property_id="P123", value="bonjour monde"),
            ],
            "P456": [create_string_snak(property_id="P456", value="jane smith")],
        }

        new_qualifiers = {
            "P123": [create_string_snak(property_id="P123", value="ahoj svet")]
        }

        assert not are_equivalent_qualifiers(existing_qualifiers, new_qualifiers)


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


def test_non_flickr_urls_arent_equivalent() -> None:
    assert not are_equivalent_flickr_urls(
        url1="https://www.flickr.com/photos/29904699@N00/16100150",
        url2="https://www.example.net/",
    )
