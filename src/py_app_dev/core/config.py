import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, get_args, get_origin

import yaml
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from mashumaro.mixins.json import DataClassJSONMixin

from .exceptions import UserNotificationException
from .logging import logger


class BaseConfigDictMixin(DataClassDictMixin):
    class Config(BaseConfig):
        # When serializing to dict, omit fields with value None
        omit_none = True
        serialize_by_alias = True


TConfig = TypeVar("TConfig", bound="BaseConfigDictMixin")


@dataclass
class BaseConfigJSONMixin(DataClassJSONMixin):
    """Shared mixin providing mashumaro config and JSON file I/O."""

    class Config(BaseConfig):
        omit_none = True
        serialize_by_alias = True

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


class NamedElement(Protocol):
    @property
    def name(self) -> Any: ...


TNamedElement = TypeVar("TNamedElement", bound=NamedElement)


def merge_named_elements(target: list[TNamedElement], source: list[TNamedElement]) -> None:
    """Union by name: a source element with a name already in target overrides it, like git config files."""
    for element in source:
        index = next((position for position, existing in enumerate(target) if existing.name == element.name), None)

        if index is None:
            target.append(element)
        elif target[index] != element:
            logger.info(f"'{element.name}' overridden: {target[index]} -> {element}")
            target[index] = element


def parse_dict_from_file(file_path: Path) -> dict[str, Any]:
    """Parse a json/yaml configuration file into a dict, with the file named in any error."""
    try:
        match file_path.suffix:
            case ".json":
                return dict(json.loads(file_path.read_text()))
            case ".yaml" | ".yml":
                return dict(yaml.safe_load(file_path.read_text()))
            case _:
                raise UserNotificationException(f"Unsupported configuration file format '{file_path}'.")
    except UserNotificationException:
        raise
    except Exception as e:
        raise UserNotificationException(f"Failed parsing configuration file '{file_path}'.\nError: {e}") from e


TPayload = TypeVar("TPayload", bound=DataClassDictMixin)


@dataclass
class ConfigFile(Generic[TPayload]):
    """
    A parsed configuration together with the file it was loaded from.

    Keeps provenance out of the payload's wire model by composition. Subclass with a bound
    payload type (e.g. ``class MyManifestFile(ConfigFile[MyManifest])``) to use ``from_file``
    and ``from_dict``; override ``from_dict`` when the wire format nests the payload.
    """

    payload: TPayload
    #: Where the payload was loaded from; None for in-memory sources.
    file: Path | None = None

    @classmethod
    def _payload_type(cls) -> type[TPayload]:
        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is ConfigFile:
                return get_args(base)[0]
        raise TypeError(f"{cls.__name__} must subclass ConfigFile[<PayloadType>] to bind the payload type.")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(payload=cls._payload_type().from_dict(data))

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        try:
            instance = cls.from_dict(parse_dict_from_file(file_path))
        except UserNotificationException:
            raise
        except Exception as e:
            raise UserNotificationException(f"Invalid configuration file '{file_path}'.\nError: {e}") from e
        instance.file = file_path
        return instance
