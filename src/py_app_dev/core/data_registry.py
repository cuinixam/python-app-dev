from collections import defaultdict
from typing import Any, Dict, List, Type, TypeVar

T = TypeVar("T")


class DataEntry:
    """Wraps data with its provider information."""

    def __init__(self, data: Any, provider_name: str) -> None:
        self.data = data
        self.provider_name = provider_name


class DataRegistry:
    def __init__(self) -> None:
        # Registry to store data entries by type
        self._registry: Dict[Type[Any], List[DataEntry]] = defaultdict(list)

    def insert(self, data: Any, provider: str) -> None:
        """Registers a piece of information with the provider."""
        self._registry[type(data)].append(DataEntry(data, provider))

    def find_data(self, data_type: Type[T]) -> List[T]:
        """Find all data of a given type."""
        return [entry.data for entry in self.find_entries(data_type)]

    def find_entries(self, data_type: Type[T]) -> List[DataEntry]:
        """Find all data entries of a given type. Each entry contains the data and the provider."""
        return self._registry.get(data_type, [])
