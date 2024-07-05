from flickypedia.apis import WikimediaApi


class TestIsDeletedMethod:
    def test_existing_file(self, wikimedia_api: WikimediaApi) -> None:
        assert not wikimedia_api.is_deleted(filename="File:Herestraat Groningen.JPG")

    def test_deleted_file(self, wikimedia_api: WikimediaApi) -> None:
        assert wikimedia_api.is_deleted(filename="File:Mugeni Elijah.jpg")
