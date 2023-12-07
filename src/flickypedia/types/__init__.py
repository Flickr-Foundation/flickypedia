import functools
from typing import Any, Hashable, TypeVar

from pydantic import ConfigDict, TypeAdapter


T = TypeVar("T")


@functools.cache
def get_validator(model: type[T]) -> TypeAdapter[T]:
    """
    Get the validator for a given type.  This is a moderately expensive
    process, so we cache the result -- we only need to create the
    validator once for each type.
    """
    try:
        model.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore
    except AttributeError:
        pass

    return TypeAdapter(model)


def validate_typeddict(t: Any, model: type[T]) -> T:
    """
    Check that some data matches a TypedDict.

    We use this to check that the structured data we receive from
    Wikimedia matches our definitions, so we can use the data in our
    type-checked Python.

    See https://stackoverflow.com/a/77386216/1558022
    """
    # This is to fix an issue from the type checker:
    #
    #     Argument 1 to "__call__" of "_lru_cache_wrapper"
    #     has incompatible type "type[T]"; expected "Hashable"
    #
    assert isinstance(model, Hashable)

    validator = get_validator(model)

    return validator.validate_python(t, strict=True)
