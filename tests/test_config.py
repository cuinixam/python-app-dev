from dataclasses import dataclass
from typing import Any

from py_app_dev.core.config import BaseConfigDictMixin, deep_merge, merge_configs


@dataclass
class SampleConfig(BaseConfigDictMixin):
    name: str | None = None
    retries: int = 0
    nested: dict[str, Any] | None = None


def test_deep_merge():
    base = {"a": 1, "b": {"x": 1, "y": 2}, "c": 3}
    new = {"b": {"y": 200, "z": 300}, "d": 4}

    merged = deep_merge(base, new)

    assert merged == {
        "a": 1,  # preserved
        "b": {"x": 1, "y": 200, "z": 300},  # nested merged
        "c": 3,  # preserved
        "d": 4,  # added
    }


def test_merge_configs_preserves_subclass_and_merges():
    base = SampleConfig(name="service", retries=1, nested={"x": 1, "y": {"a": 10}})
    override = SampleConfig(retries=5, nested={"y": {"b": 20}, "z": 99})

    merged = merge_configs(base, override)

    assert isinstance(merged, SampleConfig)

    assert merged.name == "service", "Name should be preserved"
    assert merged.retries == 5, "Retries should be overridden"
    assert merged.nested == {"x": 1, "y": {"a": 10, "b": 20}, "z": 99}


def test_merge_configs_override_none_value():
    base = SampleConfig(name=None, retries=2, nested={"k": 1})
    override = SampleConfig(name="final", nested=None)

    merged = merge_configs(base, override)

    assert merged.name == "final", "Name should be taken from override"
    assert merged.nested == {"k": 1}, "Nested should not be overridden by None"
    assert merged.retries == 0, "Retries should be taken from the default value in override"
