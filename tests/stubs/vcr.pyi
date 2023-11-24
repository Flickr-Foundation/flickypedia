import contextlib

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    filter_headers: list[str] | None = None,
    filter_query_parameters: list[str] | None = None,
) -> contextlib.AbstractContextManager[None]: ...
