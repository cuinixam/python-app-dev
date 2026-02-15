import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from mashumaro.mixins.json import DataClassJSONMixin


class BaseConfigDictMixin(DataClassDictMixin):
    class Config(BaseConfig):
        # When serializing to dict, omit fields with value None
        omit_none = True


TConfig = TypeVar("TConfig", bound="BaseConfigDictMixin")


@dataclass
class BaseConfigJSONMixin(DataClassJSONMixin):
    """Shared mixin providing mashumaro config and JSON file I/O."""

    class Config(BaseConfig):
        omit_none = True

    @classmethod
    def from_json_file(cls, file_path: Path) -> Self:
        return cls.from_dict(json.loads(file_path.read_text()))

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        match file_path.suffix:
            case ".json":
                return cls.from_json_file(file_path)
            case _:
                raise ValueError(f"Unsupported format: {file_path.suffix}")

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_string(self) -> str:
        return self.to_json_string()

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(self.to_json_string())

    def to_file(self, file_path: Path) -> None:
        self.to_json_file(file_path)


def deep_merge(base_dict: dict[Any, Any], new_dict: dict[Any, Any]) -> dict[Any, Any]:
    """Recursively merge two dictionaries, where values in new_dict override values in base_dict."""
    result: dict[Any, Any] = {}
    for key, value in base_dict.items():
        result[key] = value
    for key, value in new_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_configs(base: TConfig, override: TConfig) -> TConfig:
    merged = deep_merge(base.to_dict(), override.to_dict())
    return base.__class__.from_dict(merged)
