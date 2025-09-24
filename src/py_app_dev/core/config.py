from typing import Any, TypeVar

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


class BaseConfigDictMixin(DataClassDictMixin):
    class Config(BaseConfig):
        # When serializing to dict, omit fields with value None
        omit_none = True


TConfig = TypeVar("TConfig", bound="BaseConfigDictMixin")


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
