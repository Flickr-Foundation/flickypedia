import re


def guess_bhl_page_id(*, photo_id: str, tags: list[str]) -> str | None:
    """
    Given the metadata from the original Flickr photo, work out what
    the BHL Page ID for this photo is (if any).

    == How it works ==

    We look for a machine tag with the `bhl:page` namespace.

    BHL photos usually include a link to the page, but we can't trust
    it to point to the original photo.  Sometimes these are ambiguous --
    we don't trust these links, so we don't look at them.
    """
    candidate_page_ids = set()

    # Most BHL photos have a machine tag of the form:
    #
    #     bhl:page=33665643
    #
    # Look for any tags which match this pattern.
    for t in tags:
        m = re.match(r"^bhl:page=(?P<page_id>[0-9]+)$", t)

        if m is not None:
            candidate_page_ids.add(m.group("page_id"))

    # In general we expect that this should be an unambiguous list --
    # however, we double check to be sure!
    if not candidate_page_ids:
        print(f"Warning: no BHL page ID on {photo_id}")
        return None
    elif len(candidate_page_ids) == 1:
        return candidate_page_ids.pop()
    else:
        print(f"Warning: ambiguous BHL page ID on {photo_id} ({candidate_page_ids})")
        return None
