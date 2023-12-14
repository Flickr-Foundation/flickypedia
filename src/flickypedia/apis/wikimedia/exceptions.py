import httpx


class WikimediaApiException(Exception):
    pass


class UnknownWikimediaApiException(WikimediaApiException):
    def __init__(self, resp: httpx.Response) -> None:
        error_info = resp.json()["error"]

        self.code = error_info.get("code")
        self.error_info = error_info
        super().__init__(error_info)


class InvalidAccessTokenException(WikimediaApiException):
    """
    Thrown when we have invalid access credentials.
    """

    pass


class DuplicateFilenameUploadException(WikimediaApiException):
    """
    Thrown when somebody tries to upload a photo which has the same
    file as a file already on Wikimedia Commons.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(
            f"There is already a photo on Wikimedia Commons called {filename}"
        )


class DuplicatePhotoUploadException(WikimediaApiException):
    """
    Thrown when somebody tries to upload a photo which is identical to
    an existing photo.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(
            f"There is already an identical photo on Wikimedia Commons ({filename})"
        )


class MissingFileException(WikimediaApiException):
    """
    Thrown when somebody tries to look up a file that doesn't exist,
    """

    def __init__(self, filename: str) -> None:
        super().__init__(f"There is no such file on Wikimedia Commons ({filename})")
