import datetime

from flickypedia.uploads import upload_single_image


def test_upload_single_image(wikimedia_api):
    upload_single_image(
        wikimedia_api,
        photo_id="53268016608",
        user={"id": "199246608@N02", "username": "cefarrjf87", "realname": "Alex Chan"},
        filename="Thameslink Class 700 in Pride livery.jpg",
        file_caption="A Thameslink Class 700 train in the rainbow Pride livery, taken at night",
        date_taken={
            "value": datetime.datetime(2023, 9, 12, 19, 54, 32),
            "granularity": 0,
            "unknown": False,
        },
        date_posted=datetime.datetime.fromtimestamp(1697645772),
        license_id="cc-by-2.0",
        jpeg_url="https://live.staticflickr.com/65535/53268016608_5b890124fd_o_d.jpg",
    )
