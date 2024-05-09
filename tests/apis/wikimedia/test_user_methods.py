from flickypedia.apis import WikimediaApi


def test_get_userinfo(wikimedia_api: WikimediaApi) -> None:
    info = wikimedia_api.get_userinfo()

    assert info == {"id": 829939, "name": "Alexwlchan"}
