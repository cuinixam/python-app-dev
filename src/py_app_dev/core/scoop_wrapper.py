import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import cmp_to_key
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Optional

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin

from .exceptions import UserNotificationException
from .logging import logger
from .subprocess import SubprocessExecutor, which  # nosec


def _semver_compare(v1: str, v2: str) -> int:
    """
    Compare two version strings (naive semver-style).

    Returns
    -------
      -1 if v1 < v2
       0 if v1 == v2
       1 if v1 > v2

    """

    def to_int(s: Any) -> int:
        try:
            return int(s)
        except ValueError:
            return 0

    # Split on non-digit characters, ignoring empty pieces
    parts1 = [to_int(x) for x in re.split(r"[^\d]+", v1) if x]
    parts2 = [to_int(x) for x in re.split(r"[^\d]+", v2) if x]

    # Compare piecewise
    for p1, p2 in zip(parts1, parts2, strict=False):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1

    # If all matched so far, the "longer" one is bigger
    if len(parts1) < len(parts2):
        return -1
    elif len(parts1) > len(parts2):
        return 1

    return 0


class BaseConfigJSONMixin(DataClassJSONMixin):
    class Config(BaseConfig):
        omit_none = True
        serialize_by_alias = True

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(self.to_json_string())


@dataclass
class ScoopFileElement(BaseConfigJSONMixin):
    """Represents an app or bucket entry in the scoopfile.json."""

    _name_lc: Optional[str] = field(default=None, metadata=field_options(alias="name"))
    _name_uc: Optional[str] = field(default=None, metadata=field_options(alias="Name"))
    #: Source bucket
    _source_lc: Optional[str] = field(default=None, metadata=field_options(alias="source"))
    _source_uc: Optional[str] = field(default=None, metadata=field_options(alias="Source"))

    _version_lc: Optional[str] = field(default=None, metadata=field_options(alias="version"))
    _version_uc: Optional[str] = field(default=None, metadata=field_options(alias="Version"))

    @property
    def name(self) -> str:
        if self._name_uc:
            return self._name_uc
        elif self._name_lc:
            return self._name_lc
        else:
            raise UserNotificationException("ScoopApp must have a 'Name' or 'name' field defined.")

    @property
    def source(self) -> str:
        if self._source_uc:
            return self._source_uc
        elif self._source_lc:
            return self._source_lc
        else:
            raise UserNotificationException("ScoopApp must have a 'Source' or 'source' field defined.")

    @property
    def version(self) -> Optional[str]:
        if self._version_uc:
            return self._version_uc
        elif self._version_lc:
            return self._version_lc
        else:
            return None

    def __post_init__(self) -> None:
        if not self._name_lc and not self._name_uc:
            raise UserNotificationException("Scoop element must have a 'Name' or 'name' field defined.")
        if not self._source_lc and not self._source_uc:
            raise UserNotificationException("Scoop element must have a 'Source' or 'source' field defined.")

    def __hash__(self) -> int:
        return hash(f"{self.name}-{self.source}-{self.version}")

    def __str__(self) -> str:
        version_str = f", {self.version}" if self.version else ""
        return f"({self.source}, {self.name}{version_str})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScoopFileElement):
            return NotImplemented
        return self.name == other.name and self.source == other.source and self.version == other.version


@dataclass
class ScoopInstallConfigFile(BaseConfigJSONMixin):
    """Represents the structure of the scoopfile.json."""

    buckets: list[ScoopFileElement]
    apps: list[ScoopFileElement]

    @property
    def bucket_names(self) -> list[str]:
        return [bucket.name for bucket in self.buckets]

    @property
    def app_names(self) -> list[str]:
        return [app.name for app in self.apps]

    @classmethod
    def from_file(cls, scoop_file: Path) -> "ScoopInstallConfigFile":
        with open(scoop_file) as f:
            return cls.from_dict(json.load(f))


@dataclass
class InstalledScoopApp:
    #: App name
    name: str
    #: App version
    version: str
    #: App root directory
    path: Path
    #: List of bin directories relative to the app path
    bin_dirs: list[Path]
    #: List of directories relative to the app path
    env_add_path: list[Path]
    #: App scoop manifest file
    manifest_file: Path
    #: Environment variables defined in the manifest
    env_vars: dict[str, Any] = field(default_factory=dict)

    def get_bin_paths(self) -> list[Path]:
        """Return the list of absolute bin paths."""
        return [self.path.joinpath(bin_dir) for bin_dir in self.bin_dirs]

    def get_env_add_path(self) -> list[Path]:
        """Return the list of absolute env_add_path paths."""
        return [self.path.joinpath(env_add_path) for env_add_path in self.env_add_path]

    def get_all_required_paths(self) -> list[Path]:
        """Return the list of all required paths, maintaining order and removing duplicates."""
        all_paths = [*self.get_bin_paths(), *self.get_env_add_path()]
        unique_paths = list(dict.fromkeys(all_paths))
        return unique_paths


class ScoopWrapper:
    def __init__(self) -> None:
        self.logger = logger.bind()
        self.scoop_script = self._find_scoop_script()
        self.scoop_root_dir = self._find_scoop_root_dir(self.scoop_script)

    @property
    def apps_directory(self) -> Path:
        return self.scoop_root_dir.joinpath("apps")

    def install(self, scoop_file: Path) -> list[InstalledScoopApp]:
        """
        Install scoop apps from a scoop file.

        It returns a list with all apps required to be installed as installed apps.
        """
        return self.do_install(ScoopInstallConfigFile.from_file(scoop_file), self.get_installed_apps())

    def _find_scoop_script(self) -> Path:
        scoop_path = which("scoop")
        if not scoop_path:
            scoop_path = Path().home().joinpath("scoop", "shims", "scoop.ps1")
        else:
            # Use the powershell script to make sure the powershell profile is loaded (maybe there are proxy settings)
            scoop_path = scoop_path.with_suffix(".ps1")
        self.logger.info(f"Scoop executable: {scoop_path}")
        if not scoop_path.is_file():
            raise UserNotificationException("Scoop not found in PATH or user home directory. Please install Scoop and run the build script again.")
        return scoop_path

    def _find_scoop_root_dir(self, scoop_executable_path: Path) -> Path:
        pattern = r"^(.*?/scoop/)"
        match = re.match(pattern, scoop_executable_path.absolute().as_posix())

        if match:
            return Path(match.group(1))
        else:
            raise UserNotificationException(f"Could not determine scoop directory for {scoop_executable_path}.")

    def parse_bin_dirs(self, bin_data: str | list[str | list[str]]) -> list[Path]:
        """Parse the bin directory from the manifest file."""

        def get_parent_dir(bin_entry: str | list[str]) -> Path | None:
            bin_path = Path(bin_entry[0]) if isinstance(bin_entry, list) else Path(bin_entry)
            # If the bin entry is in the app root directory, return the app root directory
            if len(bin_path.parts) == 1:
                return Path(".")
            return bin_path.parent

        result = []
        if isinstance(bin_data, str):
            result = [parent for parent in [get_parent_dir(bin_data)] if parent]
        elif isinstance(bin_data, list):
            result = [parent for parent in [get_parent_dir(bin_entry) for bin_entry in bin_data] if parent]
        # Remove duplicates and maintain order
        return list(dict.fromkeys(result))

    def parse_env_path_dirs(self, env_paths: str | list[str]) -> list[Path]:
        """Parse the env_add_path directories from the manifest file."""
        if isinstance(env_paths, str):
            return [Path(env_paths)]
        elif isinstance(env_paths, list):
            return [Path(env_path) for env_path in env_paths]

    @staticmethod
    def parse_env_vars(env_set: dict[str, str], app_path: Path) -> dict[str, Any]:
        """Parse and return environment variables from the manifest."""
        return {key: value.replace("$dir", str(app_path)) for key, value in env_set.items()}

    def parse_manifest_file(self, manifest_file: Path) -> InstalledScoopApp:
        app_directory: Path = manifest_file.parent
        tool_name: str = app_directory.parent.name
        try:
            with open(manifest_file) as f:
                manifest_data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            raise UserNotificationException(f"Failed to parse manifest file: {manifest_file.as_posix()}. Error: {e}") from None

        tool_version: str = manifest_data.get("version", "")
        bin_dirs: list[Path] = self.parse_bin_dirs(manifest_data.get("bin", []))
        env_add_path: list[Path] = self.parse_env_path_dirs(manifest_data.get("env_add_path", []))
        installed_app = InstalledScoopApp(
            name=tool_name,
            version=tool_version,
            path=app_directory,
            manifest_file=manifest_file,
            bin_dirs=bin_dirs,
            env_add_path=env_add_path,
            env_vars=self.parse_env_vars(manifest_data.get("env_set", {}), app_directory),
        )
        return installed_app

    def get_installed_apps(self) -> list[InstalledScoopApp]:
        installed_tools: list[InstalledScoopApp] = []
        self.logger.info(f"Looking for installed apps in {self.apps_directory}")
        manifest_files = [file for file in self.apps_directory.glob("*/*/manifest.json") if "current" != file.parent.name]

        with ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(self.parse_manifest_file, manifest_file): manifest_file for manifest_file in manifest_files}
            for future in as_completed(future_to_file):
                installed_tools.append(future.result())

        return installed_tools

    def do_install(
        self,
        scoop_install_config: ScoopInstallConfigFile,
        installed_apps: list[InstalledScoopApp],
    ) -> list[InstalledScoopApp]:
        """Install scoop apps from a scoop file."""
        newly_installed_apps = self.do_install_missing(scoop_install_config, installed_apps)
        # If some apps where just installed we need to update the list of installed apps
        if newly_installed_apps:
            self.logger.info("New apps were installed, update the list of installed apps.")
            updated_installed_apps = self.get_installed_apps()
        else:
            updated_installed_apps = installed_apps
        apps = self.map_required_apps_to_installed_apps(scoop_install_config.apps, updated_installed_apps)
        return apps

    def do_install_missing(
        self,
        scoop_install_config: ScoopInstallConfigFile,
        installed_apps: list[InstalledScoopApp],
    ) -> list[ScoopFileElement]:
        """Check which apps are installed and install the missing ones."""
        apps_to_install = self.get_tools_to_be_installed(scoop_install_config.apps, installed_apps)
        if not apps_to_install:
            self.logger.info("All Scoop apps already installed. Skip installation.")
            return []
        already_installed_apps = set(scoop_install_config.apps) - set(apps_to_install)
        if already_installed_apps:
            self.logger.info(f"Scoop apps already installed: {','.join(str(app) for app in already_installed_apps)}")
        self.logger.info(f"Start installing missing apps: {','.join(str(app) for app in apps_to_install)}")

        # Create a temporary scoopfile with the remaining apps to install and install them
        with TemporaryDirectory() as tmp_dir:
            tmp_scoop_file = Path(tmp_dir).joinpath("scoopfile.json")
            ScoopInstallConfigFile(scoop_install_config.buckets, apps_to_install).to_json_file(tmp_scoop_file)
            self.run_powershell_command(f"{self.scoop_script} import {tmp_scoop_file}")
        return apps_to_install

    @staticmethod
    def run_powershell_command(command: str, update_ps_module_path: bool = True) -> None:
        # (!) Make sure powershell core module does not pollute the module path. Without this change scoop.ps1 fails because 'Get-FileHash' cannot be found.
        # See more details here: https://github.com/PowerShell/PowerShell/issues/8635
        ps_command = f'$env:PSModulePath=\\"$PSHOME\\Modules;$env:PSMODULEPATH\\"; {command}' if update_ps_module_path else f"{command}"
        SubprocessExecutor(f"powershell.exe -Command {ps_command}").execute()

    @staticmethod
    def map_required_apps_to_installed_apps(
        required_apps: list[ScoopFileElement],
        installed_apps: list[InstalledScoopApp],
    ) -> list[InstalledScoopApp]:
        """
        Map the required apps to the installed apps.

        If version is specified, we'll look for an exact (name, version) match.
        If version is not specified, we'll pick the "latest" version that is installed.
        """

        def _compare_installed_scoop_apps(a: InstalledScoopApp, b: InstalledScoopApp) -> int:
            return _semver_compare(b.version, a.version)

        # For quicker lookups, group installed apps by name
        installed_by_name: dict[str, list[InstalledScoopApp]] = {}
        for tool in installed_apps:
            installed_by_name.setdefault(tool.name, []).append(tool)

        # Sort each name group by version, descending (so index 0 is "highest" version)
        for name in installed_by_name:
            installed_by_name[name].sort(key=cmp_to_key(_compare_installed_scoop_apps))

        apps: list[InstalledScoopApp] = []
        for app in required_apps:
            logger.info(f"Check required app {app.name} {app.version or ''}")
            if app.name not in installed_by_name:
                raise UserNotificationException(f"Could not find any version of '{app.name}' in the installed apps. Something went wrong during the scoop installation.")

            if app.version:
                # Find the exact installed version
                match = next(
                    (tool for tool in installed_by_name[app.name] if tool.version == app.version),
                    None,
                )
                if not match:
                    raise UserNotificationException(f"Could not find '{app.name}' at version '{app.version}' in the installed apps. Installation might have failed.")
                apps.append(match)
            else:
                # Version not specified - pick the "highest" version from installed_by_name
                # (currently sorted in descending order, so index 0 is "newest")
                available_versions = [tool.version for tool in installed_by_name[app.name]]
                latest_tool = installed_by_name[app.name][0]
                logger.info(f"App '{app.name}' was required without version; using installed version '{latest_tool.version}' from {available_versions}.")
                apps.append(latest_tool)

        return apps

    @staticmethod
    def get_tools_to_be_installed(
        required_apps: list[ScoopFileElement],
        installed_apps: list[InstalledScoopApp],
    ) -> list[ScoopFileElement]:
        """Determines which apps/versions listed in the scoopfile config are not present in the list of currently installed apps."""
        # Create a set of tuples for efficient lookup of installed tools
        installed_tools_set = {(tool.name, tool.version) for tool in installed_apps if tool.version}
        apps_to_install: list[ScoopFileElement] = []
        for app in required_apps:
            logger.info(f"Check app {app.name} {app.version or ''}")
            # If version is specified in the config, check for exact match
            if app.version:
                if (app.name, app.version) not in installed_tools_set:
                    apps_to_install.append(app)
            else:
                # If no version is specified in config, check if *any* version of the app is installed.
                is_any_version_installed = any(name == app.name for name, _ in installed_tools_set)
                if not is_any_version_installed:
                    logger.warning(f"App '{app.name}' in scoopfile has no version. Will attempt install if no version is found.")
                    apps_to_install.append(app)
                else:
                    logger.info(f"App '{app.name}' required without specific version, but found an installed version. Skipping installation attempt for it.")

        return apps_to_install
