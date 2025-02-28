import contextlib

from vcr.cassette import Cassette

def use_cassette(
    cassette_name: str,
    /,
    *,
    cassette_library_dir: str,
    filter_headers: list[tuple[str, str]] | None = None,
    filter_query_parameters: list[str] | list[tuple[str, str]] | None,
    decode_compressed_response: bool,
) -> contextlib.AbstractContextManager[Cassette]: ...
