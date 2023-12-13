import datetime
import os

from flask import Flask
import pytest

from flickypedia.apis.structured_data import (
    create_copyright_status_statement,
    create_date_taken_statement,
    create_flickr_creator_statement,
    create_flickr_photo_id_statement,
    create_license_statement,
    create_location_statement,
    create_posted_to_flickr_statement,
    create_sdc_claims_for_existing_flickr_photo,
    create_sdc_claims_for_new_flickr_photo,
    create_source_data_for_photo,
)
from flickypedia.types.flickr import (
    SinglePhotoData,
    LocationInfo,
    SinglePhoto,
    TakenGranularity,
    User as FlickrUser,
)
from flickypedia.types.structured_data import NewClaims, NewStatement
from utils import get_typed_fixture


def get_claims_fixture(filename: str) -> NewClaims:
    return get_typed_fixture(
        path=os.path.join("structured_data", filename), model=NewClaims
    )


def get_statement_fixture(filename: str) -> NewStatement:
    return get_typed_fixture(
        path=os.path.join("structured_data", filename), model=NewStatement
    )


@pytest.mark.parametrize(
    ["user", "filename"],
    [
        pytest.param(
            {
                "id": "47397743@N05",
                "username": None,
                "realname": "WNDC",
                "path_alias": "west_northamptonshire_development_corporation",
                "photos_url": "https://www.flickr.com/photos/west_northamptonshire_development_corporation/",
                "profile_url": "https://www.flickr.com/people/west_northamptonshire_development_corporation/",
            },
            "creator_Q7986087.json",
            id="47397743@N05",
        ),
        pytest.param(
            {
                "id": "199246608@N02",
                "username": "Alex Chan",
                "realname": None,
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            "creator_AlexChan.json",
            id="AlexChan",
        ),
        pytest.param(
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "path_alias": "obamawhitehouse",
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            "creator_ObamaWhiteHouse.json",
            id="ObamaWhiteHouse",
        ),
    ],
)
def test_create_flickr_creator_statement(
    app: Flask, vcr_cassette: str, user: FlickrUser, filename: str
) -> None:
    result = create_flickr_creator_statement(user)
    expected = get_statement_fixture(filename)

    assert result == expected


def test_create_copyright_status_statement_fails_for_unknown_license() -> None:
    with pytest.raises(ValueError, match="Unable to map a copyright status"):
        create_copyright_status_statement(license_id="cc-by-nc-2.0")


@pytest.mark.parametrize(
    ["license_id", "filename"],
    [
        ("cc-by-2.0", "copyright_status_copyrighted.json"),
        ("cc-by-sa-2.0", "copyright_status_copyrighted.json"),
        ("usgov", "copyright_status_usgov.json"),
        ("cc0-1.0", "copyright_status_public_domain.json"),
        ("pdm", "copyright_status_public_domain.json"),
    ],
)
def test_create_copyright_status_statement(license_id: str, filename: str) -> None:
    result = create_copyright_status_statement(license_id=license_id)
    expected = get_statement_fixture(filename)

    assert result == expected


def test_create_source_data_for_photo() -> None:
    result = create_source_data_for_photo(
        photo_id="53248015596",
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        retrieved_at=datetime.datetime(2023, 11, 14, 16, 15, 0),
    )
    expected = get_statement_fixture(filename="photo_source_data.json")

    assert result == expected


def test_create_source_data_without_retrieved_at() -> None:
    result = create_source_data_for_photo(
        photo_id="53248015596",
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        retrieved_at=None,
    )
    expected = get_statement_fixture(filename="photo_source_data_without_date.json")

    assert result == expected


@pytest.mark.parametrize(
    ["license_id", "filename"],
    [
        ("cc-by-2.0", "license_cc_by_2.0.json"),
        ("usgov", "license_usgov.json"),
        ("cc0-1.0", "license_cc0.json"),
    ],
)
def test_create_license_statement(license_id: str, filename: str) -> None:
    actual = create_license_statement(license_id)
    expected = get_statement_fixture(filename)

    assert actual == expected


def test_can_create_license_statement_for_all_allowed_licenses(app: Flask) -> None:
    for license_id in app.config["ALLOWED_LICENSES"]:
        create_license_statement(license_id)


def test_create_license_statement_fails_if_unrecognised_license() -> None:
    with pytest.raises(ValueError, match="Unrecognised license ID"):
        create_license_statement(license_id="mystery")


def test_create_posted_to_flickr_statement() -> None:
    actual = create_posted_to_flickr_statement(
        date_posted=datetime.datetime(2023, 10, 12)
    )
    expected = get_statement_fixture(filename="date_posted_to_flickr.json")

    assert actual == expected


@pytest.mark.parametrize(
    ["date_taken", "granularity", "filename"],
    [
        # Based on https://www.flickr.com/photos/184374196@N07/53069446440
        (
            datetime.datetime(2023, 2, 20, 23, 32, 31),
            "second",
            "date_taken_YYYY-MM-DD.json",
        ),
        # Based on https://www.flickr.com/photos/normko/361850789
        (datetime.datetime(1970, 3, 1, 0, 0, 0), "month", "date_taken_YYYY-MM.json"),
        # Based on https://www.flickr.com/photos/nationalarchives/5240741057
        (datetime.datetime(1950, 1, 1, 0, 0, 0), "year", "date_taken_YYYY.json"),
        # Based on https://www.flickr.com/photos/nlireland/6975991819
        (datetime.datetime(1910, 1, 1, 0, 0, 0), "circa", "date_taken_circa.json"),
    ],
)
def test_create_date_taken_statement(
    date_taken: datetime.datetime, granularity: TakenGranularity, filename: str
) -> None:
    actual = create_date_taken_statement(
        date_taken={"value": date_taken, "granularity": granularity}
    )
    expected = get_statement_fixture(filename)

    assert actual == expected


def test_create_date_taken_statement_fails_on_unrecognised_granularity() -> None:
    with pytest.raises(ValueError, match="Unrecognised taken_granularity"):
        create_date_taken_statement(
            date_taken={
                "value": datetime.datetime.now(),
                "granularity": -1,  # type: ignore
                "unknown": False,
            }
        )


class TestCreateLocationStatement:
    def test_unrecognised_location_accuracy_is_error(self) -> None:
        with pytest.raises(ValueError, match="Unrecognised location accuracy"):
            create_location_statement(
                location={"latitude": 8.079310, "longitude": 77.550004, "accuracy": -1}
            )

    @pytest.mark.parametrize(
        ["location", "filename"],
        [
            (
                {"latitude": 9.135158, "longitude": 40.083811, "accuracy": 16},
                "location_ethiopia.json",
            ),
        ],
    )
    def test_create_location_statement(
        self, location: LocationInfo, filename: str
    ) -> None:
        actual = create_location_statement(location=location)
        expected = get_statement_fixture(filename)

        assert actual == expected

    def test_omits_location_statement_if_photo_has_no_location_data(self) -> None:
        data = get_typed_fixture(
            path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
        )

        sdc = create_sdc_claims_for_new_flickr_photo(
            photo=data["photos"][0], retrieved_at=data["retrieved_at"]
        )

        assert not any(
            statement["mainsnak"]["property"] == "P1259" for statement in sdc["claims"]
        )

    def test_includes_location_statement_if_photo_has_location_data(self) -> None:
        data = get_typed_fixture(
            path="flickr_api/single_photo-52994452213.json", model=SinglePhotoData
        )

        sdc = create_sdc_claims_for_new_flickr_photo(
            photo=data["photos"][0], retrieved_at=data["retrieved_at"]
        )

        location_statements = [
            statement
            for statement in sdc["claims"]
            if statement["mainsnak"]["property"] == "P1259"
        ]

        assert len(location_statements) == 1


def test_create_flickr_photo_id_statement() -> None:
    statement = create_flickr_photo_id_statement(photo_id="1234567")

    assert statement == {
        "mainsnak": {
            "datavalue": {"value": "1234567", "type": "string"},
            "property": "P12120",
            "snaktype": "value",
        },
        "type": "statement",
    }


def test_create_sdc_claims_for_flickr_photo_without_date_taken(
    app: Flask, vcr_cassette: str
) -> None:
    photo: SinglePhoto = {
        "id": "53248015596",
        "url": "https://www.flickr.com/photos/199246608@N02/53248015596/",
        "owner": {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "path_alias": None,
            "photos_url": "https://www.flickr.com/photos/199246608@N02/",
            "profile_url": "https://www.flickr.com/people/199246608@N02/",
        },
        "title": "IMG_6027",
        "description": None,
        "sizes": [
            {
                "label": "Original",
                "source": "https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
                "media": "photo",
                "width": 4032,
                "height": 3024,
            }
        ],
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "date_posted": datetime.datetime.fromtimestamp(1696939706),
        "date_taken": None,
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime.datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53248015596.json")

    assert actual == expected


def test_create_sdc_claims_for_flickr_photo_with_date_taken(
    app: Flask, vcr_cassette: str
) -> None:
    photo: SinglePhoto = {
        "id": "53234140350",
        "url": "https://www.flickr.com/photos/mdgovpics/53234140350/",
        "owner": {
            "id": "64018555@N03",
            "username": "MDGovpics",
            "realname": "Maryland GovPics",
            "path_alias": "mdgovpics",
            "photos_url": "https://www.flickr.com/photos/mdgovpics/",
            "profile_url": "https://www.flickr.com/people/mdgovpics/",
        },
        "title": "UMD Class Visits",
        "description": "Lt. Governor Aruna visits classes at University of Maryland by Joe Andrucyk at Thurgood Marshall Hall, 7805 Regents Dr, College Park MD 20742",
        "sizes": [
            {
                "label": "Original",
                "source": "https://live.staticflickr.com/65535/53234140350_93579322a9_o_d.jpg",
                "media": "photo",
                "width": 6192,
                "height": 4128,
            }
        ],
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "date_posted": datetime.datetime.fromtimestamp(1696421915),
        "date_taken": {
            "value": datetime.datetime(2023, 10, 3, 5, 45, 0),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime.datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53234140350.json")

    assert actual == expected


def test_it_creates_sdc_for_photo_with_in_copyright_license(vcr_cassette: str) -> None:
    photo: SinglePhoto = {
        "id": "15602283025",
        "url": "https://www.flickr.com/photos/golfking1/15602283025/",
        "owner": {
            "id": "57778372@N04",
            "username": "airplanes_uk",
            "realname": "Jonathan Palombo",
            "path_alias": "golfking1",
            "photos_url": "https://www.flickr.com/photos/golfking1/",
            "profile_url": "https://www.flickr.com/people/golfking1/",
        },
        "title": "EI-DYY",
        "description": None,
        "sizes": [
            {
                "label": "Large 1024",
                "source": "https://live.staticflickr.com/3943/15602283025_fd7d8b0dd9_b.jpg",
                "media": "photo",
                "width": 1024,
                "height": 839,
            }
        ],
        "license": {"id": "in-copyright", "label": "All Rights Reserved", "url": None},
        "date_posted": datetime.datetime.fromtimestamp(1414001923),
        "date_taken": {
            "value": datetime.datetime(2014, 7, 14, 7, 56, 51),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
    }

    actual = create_sdc_claims_for_existing_flickr_photo(photo)
    expected = get_claims_fixture("photo_15602283025.json")

    assert actual == expected
