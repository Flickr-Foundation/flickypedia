from flickypedia.apis.wikitext import create_wikitext


def test_create_wikitext_for_photo():
    actual = create_wikitext(
        license_id="cc-by-2.0",
    )
    expected = """=={{int:filedesc}}==
{{Information}}

=={{int:license-header}}==
{{cc-by-2.0}}
"""

    assert actual == expected
