import pytest

from flickypedia.apis.wikimedia import WikimediaApi, WikimediaApiException


def test_get_userinfo(wikimedia_api):
    info = wikimedia_api.get_userinfo()

    assert info == {"id": 829939, "name": "Alexwlchan"}


def test_get_userinfo_with_bad_token():
    broken_api = WikimediaApi(access_token="not_a_real_token")

    with pytest.raises(WikimediaApiException, match="Invalid access token") as exc:
        broken_api.get_userinfo()

    assert exc.value.code == "mwoauth-invalid-authorization"
