import bs4
from flask import render_template
import pytest

from flickypedia.apis.structured_data import create_flickr_creator_statement


def test_gets_creator_html(app):
    # statement = create_flickr_creator_statement(user={'id': })
    pass
