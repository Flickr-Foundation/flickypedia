import http.cookiejar

class PywikibotCookieJar(http.cookiejar.LWPCookieJar):
    def load(
        self,
        user: str | None = ...,
        ignore_discard: bool = ...,
        ignore_expires: bool = ...,
    ) -> None: ...
