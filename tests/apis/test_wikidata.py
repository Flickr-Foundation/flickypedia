import pytest

from flickypedia.apis.wikidata import lookup_flickr_user_in_wikidata


@pytest.mark.parametrize(["id", "name", "wikidata_id"], [
    # These first two examples come from the Wikidata property page for
    # "Flickr user ID".  See https://www.wikidata.org/wiki/Property:P3267#P1855
    #
    # In the case of "130608600@N05" (SpaceX), I don't think the SPARQL
    # query can find it because the value has "deprecated rank" [1].
    # I think it's correct for us not to return values with deprecated rank --
    # it's better for this function not to return anything than to return
    # something correct.
    #
    # [1]: https://www.wikidata.org/wiki/Help:Ranking#Deprecated_rank
    ("199246608@N02", "ianemes", "Q5981474"),
    ("130608600@N05", None, None),

    # This is an example I found by searching Google with the query
    #
    #     site:wikidata.org "Flickr user ID"
    #
    # to find other examples of this in use.
    ("47397743@N05", None, "Q7986087"),

    # This is a Flickr user I created for testing Flickypedia, which is
    # brand new and definitely shouldn't exist in Wikidata.
    ("199246608@N02", None, None),

    # This is a somewhat pathological case -- I'm using a user ID and name
    # that both appear in Wikidata, but for different users.  This causes
    # the Wikidata query to return two results.
    #
    # In this case, the correct thing for the function to do is to return
    # nothing, because it can't determine which is correct.
    ("47397743@N05", "ianemes", None)
])
def test_lookup_flickr_user_in_wikidata(vcr_cassette, id, name, wikidata_id):
    assert lookup_flickr_user_in_wikidata(id=id, name=name) == wikidata_id