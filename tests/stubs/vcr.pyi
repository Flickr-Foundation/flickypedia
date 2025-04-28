import contextlib
import typing

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    *,
    filter_headers: list[str] | None = None,
    filter_query_parameters: list[str] | None = None,
    decode_compressed_response: typing.Literal[True],
) -> contextlib.AbstractContextManager[None]: ...
