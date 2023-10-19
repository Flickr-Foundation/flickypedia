from flask import Flask
from flask_login import FlaskLoginClient, LoginManager
import pytest

from flickypedia import create_app
from flickypedia.views.find_photos import find_photos
from flickypedia.utils import a_href

class TestUser:
    def __init__(self, name):
        self.name = name

    def get_id(self):
        return 1

@pytest.fixture
def client():
    flask_app = create_app(template_folder='/users/alexwlchan/repos/flickypedia/src/flickypedia/templates')

    flask_app.test_client_class = FlaskLoginClient

    with flask_app.test_client(user=TestUser(name='example')) as test_client:
        yield test_client


def test_find_photos(client):
    resp = client.get('/find_photos')

    print(resp)

    assert 0