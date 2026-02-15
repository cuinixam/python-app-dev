"""Utility functions for working with collections and type filtering."""

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def find_elements_of_type(elements: list[Any], element_type: type[T]) -> list[T]:
    """Find all elements of a specific type."""
    return [elem for elem in elements if isinstance(elem, element_type)]


def filter_elements(elements: list[T], filter_fn: Callable[[T], bool]) -> list[T]:
    """Filter elements based on a predicate function."""
    return [elem for elem in elements if filter_fn(elem)]


def find_first_element_of_type(elements: list[Any], element_type: type[T], filter_fn: Callable[[T], bool] | None = None) -> T | None:
    """Find the first element of a specific type, optionally matching a filter condition."""
    filtered_elements = find_elements_of_type(elements, element_type)
    if filter_fn:
        filtered_elements = filter_elements(filtered_elements, filter_fn)
    return filtered_elements[0] if filtered_elements else None
