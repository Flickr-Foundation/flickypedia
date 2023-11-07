import contextlib
from typing import List, Optional

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    filter_query_parameters: Optional[List[str]] = None,
) -> contextlib.AbstractContextManager[None]: ...
