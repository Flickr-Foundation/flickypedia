from flickypedia.apis.wikimedia.language_methods import order_language_list


def test_order_language_list() -> None:
    results = {
        "es": "es – spanish",
        "eo": "esperanto",
        "sco": "escocès",
        "es-formal": "español (formal)",
        "sk": "esiruwaku",
        "sl": "esiruwenu",
        "myv": "esiya — èdè esiya",
        "de-ch": "esiyi-high — isijamani esiyi-high swiss",
        "str": "estrechos — salish de los estrechos",
    }

    language_list = order_language_list(query="es", results=results)

    assert language_list == [
        {"id": "es", "label": "español", "match_text": None},
        {"id": "eo", "label": "Esperanto", "match_text": None},
        {"id": "es-formal", "label": "español (formal)", "match_text": None},
        {"id": "sk", "label": "slovenčina", "match_text": "esiruwaku"},
        {"id": "sl", "label": "slovenščina", "match_text": "esiruwenu"},
        {
            "id": "de-ch",
            "label": "Schweizer Hochdeutsch",
            "match_text": "esiyi-high — isijamani esiyi-high swiss",
        },
        {"id": "sco", "label": "Scots", "match_text": "escocès"},
        {"id": "myv", "label": "эрзянь", "match_text": "esiya — èdè esiya"},
    ]
