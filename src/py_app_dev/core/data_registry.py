from collections import defaultdict
from typing import Any, TypeVar

T = TypeVar("T")


class DataEntry:
    """Wraps data with its provider information."""

    def __init__(self, data: Any, provider_name: str) -> None:
        self.data = data
        self.provider_name = provider_name


class DataRegistry:
    def __init__(self) -> None:
        # Registry to store data entries by type (fully qualified name as the key)
        self._registry: dict[str, list[DataEntry]] = defaultdict(list)

    @staticmethod
    def _get_type_name(obj_type: type[Any]) -> str:
        """Get the fully qualified name of the type."""
        return f"{obj_type.__module__}.{obj_type.__name__}"

    def insert(self, data: Any, provider: str) -> None:
        """Registers a piece of information with the provider."""
        self._registry[self._get_type_name(type(data))].append(DataEntry(data, provider))

    def find_data(self, data_type: type[T]) -> list[T]:
        """Find all data of a given type."""
        return [entry.data for entry in self.find_entries(data_type)]

    def find_entries(self, data_type: type[T]) -> list[DataEntry]:
        """Find all data entries of a given type. Each entry contains the data and the provider."""
        return self._registry.get(self._get_type_name(data_type), [])
