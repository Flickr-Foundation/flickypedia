"""
Methods used for validating metadata in the upload form.
"""

import typing

from .base import WikimediaApiBase
from .exceptions import UnknownWikimediaApiException


class TitleValidationResult:
    Ok = typing.TypedDict("Ok", {"result": typing.Literal["ok"]})
    Failed = typing.TypedDict(
        "Failed",
        {
            "result": typing.Literal["blacklisted", "duplicate", "invalid", "too_long"],
            "text": str,
        },
    )


TitleValidation = TitleValidationResult.Ok | TitleValidationResult.Failed


class ValidatorMethods(WikimediaApiBase):
    def validate_title(self, title: str) -> TitleValidation:
        """
        Given the name of a title, check whether it's allowed as
        a title for a new file on Wikimedia Commons.

        We try to rely on the Wikimedia APIs to do this for us, rather
        than duplicating their logic -- it's slower, but it saves us
        from having to maintain our own copy of the logic (which would
        inevitably be slightly wrong or broken).

        Instead, we do similar checks to the File Upload Wizard.
        I opened the Upload Wizard in my browser, then I used the
        developer tools to observe the API requests going back and
        forth to check whether the title was okay.

        The current result from this function is always a dict like:

                {'result': 'duplicate|blacklisted|invalid|ok|…'}

        The theory is that at some point we might add additional keys
        to this dictionary, e.g. with more detailed error information.

        """
        assert title.startswith("File:")

        # There's a maximum length of 240 bytes for UTF-8 encoded filenames
        # in Wikimedia Commons.
        #
        # See https://commons.wikimedia.org/wiki/Commons:File_naming#Length
        length_in_bytes = len(title.encode("utf8"))

        if length_in_bytes > 240:
            return {
                "result": "too_long",
                "text": "This title is too long. Please choose a title which is less than 240 bytes.",
            }

        # Check to see if the user has added their own suffix to the
        # filename, as well as the one we've added automatically.
        #
        # Wikimedia Commons will reject a file named this way with a slightly
        # unhelpful message; let's provide a better one.
        base_name = title.replace("File:", "").rsplit(".", 1)[0]

        if base_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff")
        ):
            return {
                "result": "invalid",
                "text": "Please remove the filename suffix; it will be added automatically.",
            }

        # Check for illegal characters, as defined by the wgIllegalFileChars
        # setting -- these are blocked by the Upload Wizard.
        #
        # See https://www.mediawiki.org/wiki/Manual:$wgIllegalFileChars
        # See https://til.alexwlchan.net/wmc-allowed-title-characters/
        if any(char in base_name for char in ":/\\"):
            return {
                "result": "invalid",
                "text": "This title is invalid. Make sure to remove characters like square brackets, colons, slashes, comparison operators, pipes and curly brackets.",
            }

        # Check for other pages with this title -- are we going to
        # duplicate an existing file?
        #
        # If the file exists, we'll get the ID of the existing page in
        # the `pages` list in the response:
        #
        #     {"query": {"pages": {"139632053": {…}}}}
        #
        # If the file doesn't exist, we'll get "-1" as the ID:
        #
        #     {"query": {"pages": {"-1": {…}}}}
        #
        existing_title_resp = self._get_json(
            params={"action": "query", "titles": title, "prop": "info"}
        )

        if existing_title_resp["query"]["pages"].keys() != {"-1"}:
            return {
                "result": "duplicate",
                "text": (
                    "Please choose a different title. "
                    f"There is already <a href='https://commons.wikimedia.org/wiki/{title}'>a file on Commons</a> with that title."
                ),
            }

        # Do a match for other pages with an equivalent filename -- the
        # title search in the previous test is case-sensitive.
        #
        # e.g. if there's an existing file called "Cat.JPG", then you can't
        # upload a new file called "Cat.jpg".
        #
        # Note that we do a slightly different search from the Wikimedia
        # Upload Wizard -- it uses the ``query`` action, but we use the
        # ``opensearch`` action to do case insensitive searches.
        #
        # See https://en.wikipedia.org/wiki/Wikipedia:File_names
        #
        base_title, _ = title.replace("File:", "").rsplit(".", 1)
        xml = self._get_xml(
            params={
                "action": "opensearch",
                "limit": "10",
                "search": base_title,
                # Here "14" is the namespace for categories; see
                # https://commons.wikimedia.org/wiki/Help:Namespaces
                "namespace": "6",
            },
        )

        # The XML response is of the form:
        #
        #     <SearchSuggestion xmlns="http://opensearch.org/searchsuggest2" version="2.0">
        #       <Query xml:space="preserve">tower Bridge at Night</Query>
        #       <Section>
        #         <Item>
        #           <Text xml:space="preserve">File:Tower Bridge at night (32658848243).jpg</Text>
        #           …
        #         </Item>
        #         <Item>…</Item>
        #         <Item>…</Item>
        #
        # We're interested in looking for <Text> elements with a filename
        # that matches ours, but case-insensitive.
        namespaces = {"": "http://opensearch.org/searchsuggest2"}

        for text_elem in xml.findall(".//Text", namespaces=namespaces):
            this_filename = text_elem.text
            assert this_filename is not None

            if this_filename.lower() == title.lower():
                return {
                    "result": "duplicate",
                    "text": (
                        "Please choose a different title. "
                        f"There is already a file <a href='https://commons.wikimedia.org/wiki/{this_filename}'>{this_filename.replace('File:', '')}</a> on Commons."
                    ),
                }

        # Second check to see if the title is blocked.
        #
        # This could be if e.g. the title is too long, or too short, or
        # contains forbidden characters.
        #
        # If the title is blacklisted, we'll get a response like:
        #
        #     {
        #       "titleblacklist": {
        #         "result": "blacklisted",
        #         "reason":"<p>The file name you were trying to upload
        #                   has been [[c:MediaWiki:Titleblacklist|blacklisted]]
        #                   because it is very common, uninformative, or
        #                   spelled in ALLCAPS.
        #       …
        #     }
        #
        # If the title is invalid, we'll get a response like:
        #
        #     {
        #       "error": {
        #         "code": "invalidtitle",
        #         "info":"Bad title \"File:\".",
        #         …
        #     }
        #
        # If the title is allowed, we'll get a response:
        #
        #     {"titleblacklist":{"result":"ok"}}
        #
        # See https://www.mediawiki.org/wiki/Extension:TitleBlacklist#Testing_for_matches
        # See https://www.mediawiki.org/w/api.php?action=help&modules=titleblacklist
        #
        try:
            blacklist_resp = self._get_json(
                params={
                    "action": "titleblacklist",
                    "tbaction": "create",
                    "tbtitle": title,
                }
            )
        except UnknownWikimediaApiException as exc:
            if exc.code == "invalidtitle":
                return {
                    "result": "invalid",
                    "text": "Please choose a different, more descriptive title.",
                }
            else:  # pragma: no cover
                raise

        if blacklist_resp["titleblacklist"]["result"] != "ok":
            return {
                "result": "blacklisted",
                "text": "Please choose a different, more descriptive title.",
            }

        return {"result": "ok"}
