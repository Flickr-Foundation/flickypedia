"""
Temporary workarounds for flickr-photos-api.

Remove this module once flickr-photos-api handles Flickr API changes.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from flickr_api import FlickrApi
from nitrate.xml import find_required_elem


def _ensure_usage_attributes(info_resp: ET.Element) -> None:
    """
    Flickr stopped always returning ``canprint`` on ``<usage>`` elements.

    The library treats it as required; default missing attributes so parsing
    does not fail. Flickypedia does not use these fields.
    """
    photo_elem = find_required_elem(info_resp, path=".//photo")

    for usage_elem in photo_elem.findall("usage"):
        usage_elem.attrib.setdefault("canprint", "0")


_patched = False


def apply_flickr_api_patches() -> None:
    global _patched

    if _patched:
        return

    original = FlickrApi.parse_single_photo_info

    def parse_single_photo_info(
        self: FlickrApi, info_resp: ET.Element, *, photo_id: str
    ):
        _ensure_usage_attributes(info_resp)
        return original(self, info_resp, photo_id=photo_id)

    FlickrApi.parse_single_photo_info = parse_single_photo_info  # type: ignore[method-assign]
    _patched = True
