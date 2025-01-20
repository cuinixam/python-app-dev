from dataclasses import dataclass

from py_app_dev.core.data_registry import DataRegistry


class Provider1:
    pass


@dataclass
class SomeData:
    name: str


def test_insert_and_find_data():
    registry = DataRegistry()
    registry.insert(SomeData("new data"), "TestProvider1")
    registry.insert(123, "provider2")

    string_data = registry.find_data(SomeData)
    assert len(string_data) == 1
    assert string_data[0].name == "new data"

    int_data = registry.find_data(int)
    assert int_data == [123]


def test_insert_and_find_entries():
    registry = DataRegistry()
    registry.insert(123, "provider2")
    registry.insert(333, Provider1.__name__)
    registry.insert("some string", Provider1.__name__)

    int_entries = registry.find_entries(int)

    assert len(int_entries) == 2
    assert int_entries[0].data == 123
    assert int_entries[0].provider_name == "provider2"
    assert int_entries[1].data == 333
    assert int_entries[1].provider_name == "Provider1"


def test_find_data_empty():
    registry = DataRegistry()
    data = registry.find_data(str)
    assert data == []
