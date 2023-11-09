from flickypedia.apis.wikitext import create_wikitext


def test_create_wikitext_for_photo() -> None:
    actual = create_wikitext(license_id="cc-by-2.0", categories=["Trains", "Fish"])
    expected = """=={{int:filedesc}}==
{{Information}}

=={{int:license-header}}==
{{cc-by-2.0}}

[[Category:Trains]]
[[Category:Fish]]"""

    assert actual == expected
