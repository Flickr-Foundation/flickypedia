import abc
import json
import typing
from xml.etree import ElementTree as ET

import httpx

from .exceptions import InvalidAccessTokenException, UnknownWikimediaApiException


class WikimediaApiBase(abc.ABC):
    """
    This is a basic model for Wikimedia API implementations: they have
    to provide a ``_request()`` method that takes a Wikimedia API method
    and parameters, and returns the parsed JSON.

    We deliberately split out the interface and implementation here --
    currently we use httpx, but this abstraction would make it easier
    for us to swap out the underlying HTTP framework if we wanted to.
    """

    @abc.abstractmethod
    def _request(
        self,
        *,
        method: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """
        Call an HTTP endpoint and return the text content of the response.
        """
        raise NotImplementedError

    def _get_json(self, *, params: dict[str, str]) -> typing.Any:
        """
        GET an HTTP endpoint with the given parameters and return JSON.
        """
        resp = self._request(method="GET", params={**params, "format": "json"})

        return json.loads(resp)

    def _get_xml(self, *, params: dict[str, str]) -> ET.Element:
        """
        GET an HTTP endpoint with the given parameters and return JSON.
        """
        resp = self._request(method="GET", params={**params, "format": "xml"})

        return ET.fromstring(resp)

    def _post_json(
        self, data: dict[str, str], timeout: int | None = None
    ) -> typing.Any:
        """
        POST to an HTTP endpoint with the given parameters and return JSON.

        This includes fetching the CSRF token, which is required for any
        POST call to the Wikimedia Commons API.
        """
        resp = self._request(
            method="POST",
            data={**data, "format": "json", "token": self.get_csrf_token()},
            timeout=timeout,
        )

        return json.loads(resp)

    def get_csrf_token(self) -> str:
        """
        Get a CSRF token from the Wikimedia API.

        This is required for certain API actions that modify data in
        Wikimedia.  External callers are never expected to use this,
        but functions from this class will call it when they need a token.

        See https://www.mediawiki.org/wiki/API:Tokens
        """
        resp = self._get_json(
            params={"action": "query", "meta": "tokens", "type": "csrf"}
        )

        return resp["query"]["tokens"]["csrftoken"]  # type: ignore

    # TODO: Add _get_xml here


class HttpxImplementation(WikimediaApiBase):
    """
    This is an auth-agnostic implementation of some Wikimedia API methods.

    Callers are responsible for creating an ``httpx.Client`` instance which
    is appropriately authenticated with the Wikimedia API.  This class is
    designed to be used with any auth approach.

    See https://api.wikimedia.org/wiki/Authentication
    """

    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def _request(
        self,
        *,
        method: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> typing.Any:
        resp = self.client.request(
            method,
            url="https://commons.wikimedia.org/w/api.php",
            params=params,
            data=data,
            timeout=timeout,
        )

        # When something goes wrong, we get an ``error`` key in the response.
        #
        # Detect this here and throw an exception, so callers can assume
        # there was no issue if this returns cleanly.
        #
        # See https://www.mediawiki.org/wiki/Wikibase/API#Response
        try:
            error = resp.json()["error"]

            if error["code"] == "mwoauth-invalid-authorization":
                raise InvalidAccessTokenException(error["info"])
            else:
                raise UnknownWikimediaApiException(resp)
        except (json.JSONDecodeError, KeyError):
            pass

        return resp.text
