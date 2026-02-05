from abc import ABC, abstractmethod
from pathlib import Path

from .logging import logger


class EnvSetupScriptGenerator(ABC):
    """Abstract base class for generating environment setup scripts."""

    def __init__(self, install_dirs: list[Path], environment: dict[str, str], output_file: Path):
        self.logger = logger.bind()
        self.install_dirs = install_dirs
        self.environment = environment
        self.output_file = output_file

    @abstractmethod
    def generate_content(self) -> str:
        """Generates the script content as a string."""
        pass

    def to_string(self) -> str:
        return self.generate_content()

    def to_file(self) -> None:
        content = self.generate_content()
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(content)
        self.logger.info(f"Script written to {self.output_file}")


class BatEnvSetupScriptGenerator(EnvSetupScriptGenerator):
    """Generates a batch script to set environment variables and update PATH."""

    def generate_content(self) -> str:
        """Generates the non-verbose .bat script content."""
        lines = ["@echo off"]

        # Set environment variables using self.environment
        for key, value in self.environment.items():
            # Quote the assignment for robustness
            lines.append(f'set "{key}={value}"')

        if self.install_dirs:
            path_string = ";".join([str(path) for path in self.install_dirs])
            # Prepend to existing PATH
            lines.append(f'set "PATH={path_string};%PATH%"')
        else:
            self.logger.debug("No install directories provided for PATH update.")
        lines.append("")

        return "\n".join(lines)


class Ps1EnvSetupScriptGenerator(EnvSetupScriptGenerator):
    """Generates a powershell script to set environment variables and update PATH."""

    def generate_content(self) -> str:
        lines = []

        for key, value in self.environment.items():
            # Escape backticks (`) and dollar signs ($) within double-quoted strings in PS.
            escaped_value = value.replace("`", "``").replace("$", "`$")
            # Use double quotes for the value
            lines.append(f'$env:{key}="{escaped_value}"')

        if self.install_dirs:
            path_string = ";".join([str(path) for path in self.install_dirs])
            lines.append(f'$newPaths = "{path_string}"')
            lines.append("$env:PATH = $newPaths + [System.IO.Path]::PathSeparator + $env:PATH")
        else:
            self.logger.debug("No install directories provided for PATH update.")
        lines.append("")

        return "\n".join(lines)


class ShEnvSetupScriptGenerator(EnvSetupScriptGenerator):
    """Generates a bash/sh script to set environment variables and update PATH."""

    def generate_content(self) -> str:
        lines = ["#!/bin/bash"]

        for key, value in self.environment.items():
            # Escape single quotes by replacing ' with '\''
            # This closes the string, adds an escaped quote, then reopens the string
            escaped_value = value.replace("'", "'\\''")
            # Use single quotes for the value to prevent variable expansion
            lines.append(f"export {key}='{escaped_value}'")

        if self.install_dirs:
            path_string = ":".join([str(path) for path in self.install_dirs])
            # Escape single quotes in paths
            escaped_path_string = path_string.replace("'", "'\\''")
            lines.append(f"export PATH='{escaped_path_string}':\"$PATH\"")
        else:
            self.logger.debug("No install directories provided for PATH update.")
        lines.append("")

        return "\n".join(lines)
