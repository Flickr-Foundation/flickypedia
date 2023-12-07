from typing import Any, TypeVar

from pydantic import ConfigDict, TypeAdapter


T = TypeVar("T")


def validate_typeddict(t: Any, model: type[T]) -> T:
    """
    Check that some data matches a TypedDict.

    We use this to check that the structured data we receive
    from Wikimedia matches our definitions, so we can use it
    in type-checked Python.

    See https://stackoverflow.com/a/77386216/1558022
    """
    try:
        model.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore
    except AttributeError:
        pass

    TypedDictValidator = TypeAdapter(model)
    return TypedDictValidator.validate_python(t, strict=True)
