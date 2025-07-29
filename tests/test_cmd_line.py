from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union

import pytest

from py_app_dev.core.cmd_line import (
    Command,
    CommandLineHandlerBuilder,
    is_type_optional,
    register_arguments_for_config_dataclass,
)
from py_app_dev.core.docs_utils import validates


class MockCommand(Command):
    def __init__(self, name: str, description: str, arguments: list[str]) -> None:
        super().__init__(name, description)
        self.arguments = arguments
        self.called_with_args = Namespace()

    def run(self, args: Namespace) -> int:
        print(f"Running {self.name} with args {args}")
        self.called_with_args = args
        return 0

    def _register_arguments(self, parser):
        for arg in self.arguments:
            parser.add_argument(arg, help=f"Some description for {arg}.")


@validates(
    "REQ-CMDLINE_REGISTER_COMMANDS-0.0.1",
    "REQ-CMDLINE_COMMAND_ARGS-0.0.1",
    "REQ-CMDLINE_COMMAND_EXEC-0.0.1",
)
def test_register_commands():
    builder = CommandLineHandlerBuilder(ArgumentParser())
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    cmd2 = MockCommand("cmd2", "Command 2", ["--arg3", "--arg4"])
    builder.add_command(cmd2)
    handler = builder.create()
    assert set(handler.commands) == {"cmd1", "cmd2"}
    handler.run(["cmd1", "--arg1", "value1", "--arg2", "value2"])
    assert vars(cmd1.called_with_args) == {
        "arg1": "value1",
        "arg2": "value2",
        "command": "cmd1",
    }


@validates("REQ-CMDLINE_UNKNOWN_COMMAND-0.0.1")
def test_unknown_commands():
    builder = CommandLineHandlerBuilder(ArgumentParser(exit_on_error=False))
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    handler = builder.create()
    assert handler.run(["cmdX", "--arg1", "value1"]) == 1


@validates("REQ-CMDLINE_DUPLICATION-0.0.1")
def test_duplicate_commands():
    builder = CommandLineHandlerBuilder(ArgumentParser())
    cmd1 = MockCommand("cmd1", "Command 1", ["--arg1", "--arg2"])
    builder.add_command(cmd1)
    with pytest.raises(ValueError):
        builder.add_command(cmd1)


@dataclass
class MyConfigDataclass:
    my_first_arg: Path = field(metadata={"help": "Some help for arg1."})
    arg: str = field(default="value1", metadata={"help": "Some help for arg1."})
    opt_arg: Optional[str] = field(default=None, metadata={"help": "Some help for arg1."})
    opt_arg_bool: bool | None = field(
        default=False,
        metadata={
            "help": "Some help for arg1.",
            "action": "store_true",
        },
    )


def test_is_type_optional():
    assert is_type_optional(Optional[str])
    assert not is_type_optional(str)
    assert is_type_optional(Union[Path | None, str])
    # Test modern union syntax (Python 3.10+)
    assert is_type_optional(Path | None)
    assert is_type_optional(str | None)
    assert not is_type_optional(Path | str)  # Union without None should not be optional
    assert not is_type_optional(Union[Path, str])


def test_register_arguments_for_config_dataclass():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, MyConfigDataclass)
    args = parser.parse_args(["--my-first-arg", "my/path", "--arg", "value2"])
    assert vars(args) == {
        "my_first_arg": Path("my/path"),
        "arg": "value2",
        "opt_arg": None,
        "opt_arg_bool": False,
    }


def test_register_arguments_with_action_store_true():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, MyConfigDataclass)
    args = parser.parse_args(["--my-first-arg", "my/path", "--opt-arg-bool"])
    assert vars(args) == {
        "my_first_arg": Path("my/path"),
        "arg": "value1",
        "opt_arg": None,
        "opt_arg_bool": True,
    }


@dataclass
class ClassWithOptionalPath:
    model_file: Path = field(metadata={"help": "Model file."})
    config_file: Path | None = field(default=None, metadata={"help": "Config file."})


def test_register_optional_path_arguments():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, ClassWithOptionalPath)
    args = parser.parse_args(
        [
            "--model-file",
            "my/path",
            "--config-file",
            "some/config/path",
        ]
    )
    assert vars(args) == {
        "model_file": Path("my/path"),
        "config_file": Path("some/config/path"),
    }


@dataclass
class ClassWithModernUnionTypes:
    """Test class with various modern union syntax optional fields."""

    required_path: Path = field(metadata={"help": "Required path."})
    optional_path: Path | None = field(default=None, metadata={"help": "Optional path."})
    optional_str: str | None = field(default=None, metadata={"help": "Optional string."})
    optional_int: int | None = field(default=None, metadata={"help": "Optional integer."})
    optional_bool: bool | None = field(default=None, metadata={"help": "Optional boolean."})


def test_register_modern_union_optional_arguments():
    """Test that modern union syntax (T | None) works correctly."""
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, ClassWithModernUnionTypes)

    # Test with all arguments provided
    args = parser.parse_args(
        ["--required-path", "required/path", "--optional-path", "optional/path", "--optional-str", "test_string", "--optional-int", "42", "--optional-bool", "true"]
    )
    assert vars(args) == {
        "required_path": Path("required/path"),
        "optional_path": Path("optional/path"),
        "optional_str": "test_string",
        "optional_int": 42,
        "optional_bool": True,
    }

    # Test with only required arguments
    args = parser.parse_args(["--required-path", "required/path"])
    assert vars(args) == {
        "required_path": Path("required/path"),
        "optional_path": None,
        "optional_str": None,
        "optional_int": None,
        "optional_bool": None,
    }


@dataclass
class ClassWithListArgument:
    my_paths: list[Path] = field(metadata={"help": "List of paths"})
    # This is an optional list
    my_strings: list[str] = field(default_factory=list, metadata={"help": "List of strings"})


def test_register_list_argument():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, ClassWithListArgument)
    args = parser.parse_args(
        [
            "--my-paths",
            "my/path",
            "some/other/path",
        ]
    )
    assert vars(args) == {
        "my_paths": [Path("my/path"), Path("some/other/path")],
        "my_strings": [],
    }


def test_register_list_argument_set_optional_list():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, ClassWithListArgument)
    args = parser.parse_args(
        [
            "--my-paths",
            "my/path",
            "--my-strings",
            "one",
            "two",
        ]
    )
    assert vars(args) == {
        "my_paths": [Path("my/path")],
        "my_strings": ["one", "two"],
    }


class MyEnum(Enum):
    ONE = auto()


@dataclass
class ClassWithCustomDeserialize:
    my_hex_value: int = field(
        metadata={
            "help": "My hexadecimal value.",
            "deserialize": lambda in_str: int(in_str, 16),
        }
    )
    my_int: int
    my_enum: MyEnum | None = field(metadata={"deserialize": lambda in_str: getattr(MyEnum, str(in_str).upper()) if in_str else None})


def test_register_arguments_with_custom_deserialize():
    parser = ArgumentParser()
    register_arguments_for_config_dataclass(parser, ClassWithCustomDeserialize)
    args = parser.parse_args(["--my-hex-value", "0x01", "--my-int", "13"])
    assert vars(args) == {"my_hex_value": 1, "my_int": 13, "my_enum": None}
    args = parser.parse_args(["--my-hex-value", "0x01", "--my-int", "13", "--my-enum", "one"])
    assert vars(args) == {"my_hex_value": 1, "my_int": 13, "my_enum": MyEnum.ONE}
