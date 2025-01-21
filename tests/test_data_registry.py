from pathlib import Path

from py_app_dev.core.data_registry import DataRegistry
from py_app_dev.core.pipeline import PipelineLoader, PipelineStep, PipelineStepConfig


class SomeData:
    def __init__(self, data: str):
        self.data = data


class Provider1:
    pass


def test_insert_and_find_data():
    registry = DataRegistry()
    registry.insert(SomeData("new data"), "TestProvider1")
    registry.insert(123, "provider2")

    string_data = registry.find_data(SomeData)
    assert len(string_data) == 1
    assert string_data[0].data == "new data"

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


def test_support_dynamically_loaded_classes(my_python_file: Path) -> None:
    def load_step():
        return PipelineLoader[PipelineStep]._load_steps(
            "install",
            [PipelineStepConfig(step="MyStep", file=str(my_python_file), config={"data": "value"})],
            my_python_file.parent,
        )[0]

    step_class_1st_load = load_step()._class
    step_class_2nd_load = load_step()._class
    assert step_class_1st_load != step_class_2nd_load  # Different instances
    registry = DataRegistry()
    registry.insert(step_class_1st_load(), "provider1")
    registry.insert(step_class_2nd_load(), "provider1")
    data = registry.find_data(step_class_2nd_load)
    assert len(data) == 2
