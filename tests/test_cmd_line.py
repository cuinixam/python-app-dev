from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import pytest

from py_app_dev.core.cmd_line import (
    Command,
    CommandLineHandlerBuilder,
    is_type_optional,
    register_arguments_for_config_dataclass,
)
from py_app_dev.core.docs_utils import validates


class MockCommand(Command):
    def __init__(self, name: str, description: str, arguments: List[str]) -> None:
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
    opt_arg: Optional[str] = field(
        default=None, metadata={"help": "Some help for arg1."}
    )
    opt_arg_bool: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Some help for arg1.",
            "action": "store_true",
        },
    )


def test_is_type_optional():
    assert is_type_optional(Optional[str])
    assert not is_type_optional(str)
    assert is_type_optional(Union[Optional[Path], str])
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
    config_file: Optional[Path] = field(default=None, metadata={"help": "Config file."})


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
