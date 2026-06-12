import json
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, cast, get_args, get_origin

import yaml
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from mashumaro.exceptions import InvalidFieldValue, MissingField

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


@dataclass
class SourceLocation(BaseConfigDictMixin):
    """Where a config element was parsed from (1-based line/column)."""

    file: Path | None = None
    line: int | None = None
    column: int | None = None

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


class _PositionedDict(dict[str, Any]):
    """A dict carrying its YAML position as an attribute (never a key, so passthrough payloads stay byte-clean)."""

    location: SourceLocation | None = None


def _load_positioned_yaml(file_path: Path) -> Any:
    """Parse YAML, stamping each mapping with its file:line:column."""

    # Function-local loader so the constructor never mutates the global SafeLoader.
    class _Loader(yaml.SafeLoader):
        pass

    def construct_map(loader: yaml.SafeLoader, node: yaml.MappingNode) -> Any:
        data = _PositionedDict()
        yield data
        data.update(cast(dict[str, Any], loader.construct_mapping(node)))
        data.location = SourceLocation(file_path, node.start_mark.line + 1, node.start_mark.column + 1)

    _Loader.add_constructor("tag:yaml.org,2002:map", construct_map)
    return yaml.load(file_path.read_text(), Loader=_Loader)  # noqa: S506 - _Loader subclasses SafeLoader


def _parse_dict_from_file(file_path: Path, yaml_loader: Callable[[Path], Any]) -> dict[str, Any]:
    try:
        match file_path.suffix:
            case ".json":
                data = json.loads(file_path.read_text())
            case ".yaml" | ".yml":
                data = yaml_loader(file_path)
            case _:
                raise UserNotificationException(f"Unsupported configuration file format '{file_path}'.")
    except UserNotificationException:
        raise
    except Exception as e:
        raise UserNotificationException(f"Failed parsing configuration file '{file_path}'.\nError: {e}") from e
    if not isinstance(data, dict):
        if data is None:
            found = "nothing (the file is empty)"
        elif isinstance(data, list):
            found = "a list"
        else:
            found = f"a single value ({data!r})"
        raise UserNotificationException(f"Configuration file '{file_path}' must define key/value pairs at the top level (e.g. 'name: value'), but contains {found}.")
    return data


def parse_dict_from_file(file_path: Path) -> dict[str, Any]:
    """Parse a json/yaml configuration file into a plain dict, with the file named in any error."""
    return _parse_dict_from_file(file_path, lambda path: yaml.safe_load(path.read_text()))


def parse_located_dict_from_file(file_path: Path) -> dict[str, Any]:
    """
    Parse like parse_dict_from_file, but YAML mappings carry their file:line:column as a dict attribute.

    The positions are attributes, never keys, so the dict content is identical to the plain
    parse; a ConfigElement deserialized from the result picks them up as its location.
    """
    return _parse_dict_from_file(file_path, _load_positioned_yaml)


#: Reserved provenance field on ConfigElement. The field name IS the wire key (no alias),
#: so serialization policy changes can never split the two apart.
SOURCE_LOCATION_KEY = "_source_location"

#: Per-parse stack of locations for error messages only; the top is the element
#: under construction. A stack (not a single slot) is needed so a parent scalar that
#: fails after a nested child still localizes to the parent. ContextVar → thread-safe.
_parsing_stack: ContextVar[list[SourceLocation | None] | None] = ContextVar("_config_parsing_stack", default=None)


@dataclass
class ConfigElement(BaseConfigDictMixin):
    """Base for locatable config elements: the deserializer fills the source location, serialization strips it."""

    # kw_only so subclasses keep mandatory positional fields; compare/repr off because
    # provenance is metadata, not value (equal elements from different files stay equal).
    _source_location: SourceLocation | None = field(default=None, kw_only=True, compare=False, repr=False)

    @property
    def location(self) -> SourceLocation | None:
        return self._source_location

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        annotations = cls.__dict__.get("__annotations__", {})
        for reserved_name in (SOURCE_LOCATION_KEY, "location"):
            if reserved_name in annotations:
                raise TypeError(f"{cls.__name__} must not declare a '{reserved_name}' field - it is reserved by ConfigElement for source provenance.")

    @classmethod
    def __pre_deserialize__(cls, d: dict[str, Any]) -> dict[str, Any]:
        # Push for error localization, then lift the loader's position attribute into
        # the field's key so mashumaro fills it (matching nested/list natively).
        position = getattr(d, "location", None)
        stack = _parsing_stack.get()
        if stack is not None:
            stack.append(position)  # push None too, to stay balanced with the pop
        if position is not None and SOURCE_LOCATION_KEY not in d:
            return {**d, SOURCE_LOCATION_KEY: position.to_dict()}
        return d

    @classmethod
    def __post_deserialize__(cls, obj: Self) -> Self:
        stack = _parsing_stack.get()
        if stack:
            stack.pop()  # constructed OK - drop so the top tracks the live element
        return obj

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        d.pop(SOURCE_LOCATION_KEY, None)
        return d


@contextmanager
def _located_errors(file_path: Path) -> Iterator[None]:
    """Localize mashumaro schema errors raised inside to file:line:column (file alone when unknown)."""
    token = _parsing_stack.set([])
    try:
        yield
    except (InvalidFieldValue, MissingField) as e:
        stack = _parsing_stack.get() or []
        location = next((entry for entry in reversed(stack) if entry is not None), None)
        where = str(location) if location is not None else str(file_path)
        raise UserNotificationException(f"Failed to parse configuration at {where}: {e}") from e
    finally:
        _parsing_stack.reset(token)


TElement = TypeVar("TElement", bound=ConfigElement)


def parse_config_element(element_type: type[TElement], file_path: Path) -> TElement:
    """Load a json/yaml file into a located config element; parse and schema errors name the exact position."""
    data = parse_located_dict_from_file(file_path)
    with _located_errors(file_path):
        return element_type.from_dict(data)


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
        data = parse_located_dict_from_file(file_path)
        try:
            with _located_errors(file_path):
                instance = cls.from_dict(data)
        except UserNotificationException:
            raise
        except Exception as e:
            raise UserNotificationException(f"Invalid configuration file '{file_path}'.\nError: {e}") from e
        instance.file = file_path
        return instance
