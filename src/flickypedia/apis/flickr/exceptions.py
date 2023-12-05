class FlickrApiException(Exception):
    """
    Base class for all exceptions thrown from the Flickr API.
    """

    pass


class ResourceNotFound(FlickrApiException):
    """
    Thrown when you try to look up a resource that doesn't exist.
    """

    def __init__(self, method: str, params: dict[str, str] | None):
        super().__init__(
            f"Unable to find resource at {method} with properties {params}"
        )


class LicenseNotFound(FlickrApiException):
    def __init__(self, license_id: str):
        super().__init__(f"Unable to find license with ID {license_id}")
