"""
Source-location provenance for configuration files.

A config dataclass inheriting ``ConfigElement`` knows where each element was declared,
and schema errors name the exact ``file:line:column``:

    @dataclass
    class ServerConfig(ConfigElement):
        host: str
        port: int = 8080

    config = parse_config_element(ServerConfig, Path("server.yaml"))
    config.location          # server.yaml:1:1
    config.to_dict()         # provenance never exported

Details and limits: docs/features/config.md. Each test below documents one behavior.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from py_app_dev.core.config import ConfigElement, ConfigFile, SourceLocation, parse_config_element
from py_app_dev.core.exceptions import UserNotificationException


@dataclass
class Leaf(ConfigElement):
    name: str
    level: int | None = None


@dataclass
class Doc(ConfigElement):
    leaves: list[Leaf] = field(default_factory=list)


@dataclass
class DocWithScalar(ConfigElement):
    # A located child list declared BEFORE a scalar that can fail. The scalar
    # belongs to this element, so a bad value must localize here, not to a child.
    leaves: list[Leaf] = field(default_factory=list)
    level: int | None = None


@dataclass
class DocWithPayload(ConfigElement):
    content: dict[str, Any] | None = None


class DocFile(ConfigFile[Doc]):
    pass


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def test_parse_locates_root_and_nested(tmp_path: Path) -> None:
    doc = parse_config_element(Doc, _write(tmp_path / "d.yaml", "leaves:\n  - {name: a}\n  - {name: b}\n"))
    first, second = doc.leaves
    assert doc.location is not None
    assert first.location is not None
    assert second.location is not None
    assert doc.location.line == 1
    assert first.location.line == 2
    assert second.location.line == 3
    assert first.location.file == tmp_path / "d.yaml"


def test_json_file_parses_without_locations(tmp_path: Path) -> None:
    doc = parse_config_element(Doc, _write(tmp_path / "d.json", json.dumps({"leaves": [{"name": "a"}]})))
    assert doc.leaves[0].name == "a"
    assert doc.location is None
    assert doc.leaves[0].location is None


def test_to_dict_is_provenance_free(tmp_path: Path) -> None:
    doc = parse_config_element(Doc, _write(tmp_path / "d.yaml", "leaves:\n  - {name: a, level: 3}\n"))
    assert doc.to_dict() == {"leaves": [{"name": "a", "level": 3}]}


def test_location_excluded_from_equality_and_repr() -> None:
    first = Leaf(name="a", _source_location=SourceLocation(Path("a.yaml"), 1, 1))
    second = Leaf(name="a", _source_location=SourceLocation(Path("b.yaml"), 9, 9))
    assert first == second
    assert "a.yaml" not in repr(first)


def test_passthrough_payload_stays_byte_clean(tmp_path: Path) -> None:
    # Positions ride on the dicts as attributes, never as keys, so a free-form
    # payload forwarded to another parser contains exactly what the user wrote.
    doc = parse_config_element(DocWithPayload, _write(tmp_path / "d.yaml", "content:\n  apps:\n    - {name: git}\n"))
    assert doc.location is not None
    assert doc.content == {"apps": [{"name": "git"}]}
    assert "_source_location" not in doc.content
    assert "_source_location" not in doc.content["apps"][0]


def test_config_file_carrier_locates_payload_elements(tmp_path: Path) -> None:
    doc_file = DocFile.from_file(_write(tmp_path / "d.yaml", "leaves:\n  - {name: a}\n"))
    assert doc_file.file == tmp_path / "d.yaml"
    assert doc_file.payload.location is not None
    assert doc_file.payload.leaves[0].location is not None
    assert doc_file.payload.leaves[0].location.line == 2


def test_config_file_carrier_reports_located_error(tmp_path: Path) -> None:
    bad = _write(tmp_path / "broken.yaml", "leaves:\n  - {name: a, level: not-an-int}\n")
    with pytest.raises(UserNotificationException, match=r"broken\.yaml:2:"):
        DocFile.from_file(bad)


def test_parse_error_names_file_and_field(tmp_path: Path) -> None:
    bad = _write(tmp_path / "broken.yaml", "leaves:\n  - {name: a, level: not-an-int}\n")
    with pytest.raises(UserNotificationException) as exc:
        parse_config_element(Doc, bad)
    assert "broken.yaml" in str(exc.value)
    assert "level" in str(exc.value)


def test_parse_error_pinpoints_offending_list_element_not_a_sibling(tmp_path: Path) -> None:
    # Line 2 is a VALID leaf; the bad one is on line 3. The error must point at
    # the actual culprit, not the innocent first element.
    bad = _write(tmp_path / "broken.yaml", "leaves:\n  - {name: ok}\n  - {name: a, level: not-an-int}\n")
    with pytest.raises(UserNotificationException) as exc:
        parse_config_element(Doc, bad)
    message = str(exc.value)
    assert "broken.yaml:3:" in message
    assert "broken.yaml:2:" not in message


def test_parse_error_points_at_parent_scalar_after_nested_child(tmp_path: Path) -> None:
    # The bad value is the PARENT's `level` (line 4), declared after two valid
    # located children. The error must localize to the parent element (line 1), not
    # to the last child that happened to parse just before the failure (line 3).
    # A single "deepest element" slot gets this wrong; the parse stack gets it right.
    bad = _write(tmp_path / "broken.yaml", "leaves:\n  - {name: a}\n  - {name: b}\nlevel: not-an-int\n")
    with pytest.raises(UserNotificationException) as exc:
        parse_config_element(DocWithScalar, bad)
    message = str(exc.value)
    assert "broken.yaml:1:" in message
    assert "broken.yaml:3:" not in message


def test_malformed_yaml_names_the_file(tmp_path: Path) -> None:
    bad = _write(tmp_path / "broken.yaml", "leaves: [unterminated\n")
    with pytest.raises(UserNotificationException, match="broken.yaml"):
        parse_config_element(Doc, bad)


def test_subclass_declaring_source_location_field_is_rejected() -> None:
    # The reservation is enforced at definition time, in front of whoever edits it.
    with pytest.raises(TypeError, match="reserved"):

        @dataclass
        class BadHidden(ConfigElement):
            _source_location: str = "anywhere"  # type: ignore[assignment]


def test_subclass_declaring_location_field_is_rejected() -> None:
    # A `location` field would shadow the read-only accessor property.
    with pytest.raises(TypeError, match="reserved"):

        @dataclass
        class BadVisible(ConfigElement):
            location: str = "anywhere"  # type: ignore[assignment]


def test_user_location_yaml_key_is_ignored_not_hijacked(tmp_path: Path) -> None:
    # A user field literally named `location:` hits no dataclass field at all (the
    # real field is `_source_location`), so it stays an ignored unknown key and the
    # element keeps its loader-derived provenance.
    doc = parse_config_element(Doc, _write(tmp_path / "d.yaml", "leaves:\n  - {name: a, location: somewhere}\n"))
    leaf = doc.leaves[0]
    assert leaf.name == "a"
    assert leaf.location is not None
    assert leaf.location.file == tmp_path / "d.yaml"
