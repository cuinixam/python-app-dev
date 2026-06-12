import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from py_app_dev.core.config import (
    BaseConfigDictMixin,
    BaseConfigJSONMixin,
    ConfigFile,
    deep_merge,
    merge_configs,
    merge_named_elements,
    parse_dict_from_file,
)
from py_app_dev.core.exceptions import UserNotificationException


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


@dataclass
class ConfigWithAlias(BaseConfigJSONMixin):
    internal_field: str = field(metadata={"alias": "externalName"})
    regular_field: int = 0


def test_json_mixin_serialize_by_alias() -> None:
    cfg = ConfigWithAlias(internal_field="value", regular_field=42)
    json_str = cfg.to_json_string()
    parsed = json.loads(json_str)

    assert "externalName" in parsed
    assert parsed["externalName"] == "value"
    assert "internal_field" not in parsed


# ---------- parse_dict_from_file ----------


@pytest.mark.parametrize(
    ("file_name", "content"),
    [
        ("config.json", '{"name": "app", "count": 7}'),
        ("config.yaml", "name: app\ncount: 7"),
        ("config.yml", "name: app\ncount: 7"),
    ],
)
def test_parse_dict_from_file(tmp_path: Path, file_name: str, content: str) -> None:
    file = tmp_path / file_name
    file.write_text(content)

    assert parse_dict_from_file(file) == {"name": "app", "count": 7}


@pytest.mark.parametrize(
    ("file_name", "content"),
    [
        ("config.json", "{ not valid json"),
        ("config.yaml", "key: [unclosed"),
        ("config.txt", "name: app"),
    ],
)
def test_parse_dict_from_file_errors(tmp_path: Path, file_name: str, content: str) -> None:
    file = tmp_path / file_name
    file.write_text(content)

    with pytest.raises(UserNotificationException, match=file_name):
        parse_dict_from_file(file)


# ---------- ConfigFile ----------


class SampleJsonConfigFile(ConfigFile[SampleJsonConfig]):
    pass


def test_config_file_from_file_stamps_source(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    file.write_text(json.dumps({"name": "app", "count": 7}))

    config_file = SampleJsonConfigFile.from_file(file)

    assert config_file.payload == SampleJsonConfig(name="app", count=7)
    assert config_file.file == file


def test_config_file_from_file_corrupt_raises(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    file.write_text("{ not valid json")

    with pytest.raises(UserNotificationException, match="config.json"):
        SampleJsonConfigFile.from_file(file)


def test_config_file_from_dict_has_no_source_file() -> None:
    config_file = SampleJsonConfigFile.from_dict({"name": "app"})

    assert config_file.payload.name == "app"
    assert config_file.file is None


def test_config_file_requires_bound_payload_type() -> None:
    with pytest.raises(TypeError, match="ConfigFile"):
        ConfigFile.from_dict({"name": "app"})


# ---------- merge_named_elements ----------


@dataclass
class NamedElement:
    name: str
    value: str


def test_merge_named_elements_unions_by_name() -> None:
    target = [NamedElement("first", "1")]

    merge_named_elements(target, [NamedElement("second", "2")])

    assert target == [NamedElement("first", "1"), NamedElement("second", "2")]


def test_merge_named_elements_later_overrides_earlier() -> None:
    target = [NamedElement("first", "1"), NamedElement("second", "2")]

    merge_named_elements(target, [NamedElement("first", "override")])

    assert target == [NamedElement("first", "override"), NamedElement("second", "2")]


def test_merge_named_elements_ignores_true_duplicates() -> None:
    target = [NamedElement("first", "1")]

    merge_named_elements(target, [NamedElement("first", "1")])

    assert target == [NamedElement("first", "1")]


# ---------- BaseConfigDictMixin alias ----------


@dataclass
class DictConfigWithAlias(BaseConfigDictMixin):
    internal_field: str = field(metadata={"alias": "external-name"})


def test_dict_mixin_serialize_by_alias() -> None:
    parsed = DictConfigWithAlias(internal_field="value").to_dict()

    assert parsed == {"external-name": "value"}


# ---------- End-to-end: three sources, override order, stored result ----------


@dataclass
class ToolEntry(BaseConfigJSONMixin):
    name: str
    version: str


@dataclass
class ToolsConfig(BaseConfigJSONMixin):
    tools: list[ToolEntry] = field(default_factory=list)


class ToolsConfigFile(ConfigFile[ToolsConfig]):
    pass


def test_three_config_files_merge_with_override_and_store_result(tmp_path: Path) -> None:
    base_file = tmp_path / "base.json"
    base_file.write_text(json.dumps({"tools": [{"name": "cmake", "version": "3.28.1"}, {"name": "ninja", "version": "1.11.1"}]}))
    level1_file = tmp_path / "level1.yaml"
    level1_file.write_text("tools:\n  - name: cmake\n    version: 3.29.0\n  - name: gcc\n    version: '12'")
    level2_file = tmp_path / "level2.yaml"
    level2_file.write_text("tools:\n  - name: gcc\n    version: '13'\n  - name: make\n    version: '4.4'")

    sources = [ToolsConfigFile.from_file(file) for file in (base_file, level1_file, level2_file)]
    assert [source.file for source in sources] == [base_file, level1_file, level2_file]

    merged = ToolsConfig()
    for source in sources:
        merge_named_elements(merged.tools, source.payload.tools)

    result_file = tmp_path / "merged.json"
    merged.to_json_file(result_file)

    stored = ToolsConfig.from_file(result_file)
    versions = {tool.name: tool.version for tool in stored.tools}
    # Base is the union foundation; each later file overrides by name (git-config order).
    assert versions == {"cmake": "3.29.0", "ninja": "1.11.1", "gcc": "13", "make": "4.4"}
    # The stored result is pure payload - no provenance keys leak into the file.
    assert set(json.loads(result_file.read_text()).keys()) == {"tools"}
