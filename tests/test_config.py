import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from py_app_dev.core.config import (
    BaseConfigDictMixin,
    BaseConfigJSONMixin,
    deep_merge,
    merge_configs,
)


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


# ---------- BaseConfigJSONMixin tests ----------


@dataclass
class SampleJsonConfig(BaseConfigJSONMixin):
    name: str = ""
    count: int = 0
    label: str | None = None
    metadata: dict[str, Any] | None = None


def test_json_mixin_roundtrip_file(tmp_path: Path) -> None:
    original = SampleJsonConfig(name="svc", count=3, metadata={"env": "prod"})
    file = tmp_path / "config.json"

    original.to_json_file(file)
    restored = SampleJsonConfig.from_json_file(file)

    assert restored == original


def test_json_mixin_from_file_json(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    file.write_text(json.dumps({"name": "app", "count": 7}))

    loaded = SampleJsonConfig.from_file(file)

    assert loaded.name == "app"
    assert loaded.count == 7


def test_json_mixin_from_file_unsupported(tmp_path: Path) -> None:
    file = tmp_path / "config.yaml"
    file.write_text("name: oops")

    with pytest.raises(ValueError, match=r"\.yaml"):
        SampleJsonConfig.from_file(file)


def test_json_mixin_omit_none() -> None:
    cfg = SampleJsonConfig(name="x", label=None, metadata=None)
    parsed = json.loads(cfg.to_json_string())

    assert "label" not in parsed
    assert "metadata" not in parsed


def test_json_mixin_to_string() -> None:
    cfg = SampleJsonConfig(name="a", count=1)

    assert cfg.to_string() == cfg.to_json_string()
