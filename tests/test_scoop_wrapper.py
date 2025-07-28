import json
import sys
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.scoop_wrapper import (
    InstalledScoopApp,
    ScoopFileElement,
    ScoopInstallConfigFile,
    ScoopWrapper,
    _semver_compare,
)


def create_scoop_wrapper(scoop_executable: Path | None) -> ScoopWrapper:
    """Patch the 'which' function to return a valid path to the scoop executable."""
    with patch(
        "py_app_dev.core.scoop_wrapper.which",
        return_value=scoop_executable,
    ):
        with patch(
            "pathlib.Path.home",
            return_value=scoop_executable.parent if scoop_executable else Path("some/path"),
        ):
            scoop_wrapper = ScoopWrapper()
    return scoop_wrapper


def test_scoop_installed(tmp_path: Path) -> None:
    scoop_exec = tmp_path / "scoop" / "my_scoop.ps1"
    scoop_exec.parent.mkdir(parents=True)
    scoop_exec.touch()
    scoop_wrapper = create_scoop_wrapper(scoop_exec)
    assert scoop_wrapper.scoop_script == tmp_path / "scoop" / "my_scoop.ps1"


def test_scoop_is_not_installed():
    with pytest.raises(UserNotificationException):
        create_scoop_wrapper(None)


@pytest.fixture
def scoop_dir(tmp_path: Path) -> Path:
    scoop_dir = tmp_path / "scoop"
    # Create a temporary directory structure for testing
    apps_dir = scoop_dir / "apps"
    # Create fake apps and manifest files
    manifest = apps_dir / "app1" / "current" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest_app1_ver1 = json.dumps(
        {
            "version": "1.0",
            "bin": ["bin/program1.exe", "bin/program2.exe", "program3.exe"],
        }
    )

    manifest.write_text(manifest_app1_ver1)
    manifest = apps_dir / "app1" / "1.0" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(manifest_app1_ver1)
    manifest = apps_dir / "app1" / "2.0" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"version": "2.0", "bin": [["app/program3.exe", "alias"], "program4.exe"]}))

    manifest = apps_dir / "app2" / "3.1.1" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"version": "3.1.1", "bin": "program5.exe"}))

    # new app with env_add_path
    manifest = apps_dir / "app3" / "1.0" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "version": "1.0",
                "bin": "bin/program6.exe",
                "env_add_path": "bin",
            }
        )
    )

    # some dummy manifest file somewhere in the app2 directory. This should not be picked up
    manifest = apps_dir / "app2" / "3.1.1" / "some_dir" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("dummy manifest file")

    # Create scoop executable
    scoop_ps1 = scoop_dir / "scoop.ps1"
    scoop_ps1.touch()

    return scoop_dir


def test_get_installed_tools(scoop_dir: Path) -> None:
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.ps1")

    # Get the installed tools
    installed_tools = scoop_wrapper.get_installed_apps()

    # Additional assertions based on your requirements or expectations
    assert len(installed_tools) == 4
    apps_dir = scoop_dir.joinpath("apps")

    # Check the details of individual tools
    tool = next(filter(lambda t: t.name == "app1" and t.version == "1.0", installed_tools))
    assert tool.name == "app1"
    assert tool.version == "1.0"
    assert tool.path == apps_dir.joinpath("app1/1.0")
    assert tool.manifest_file == tool.path / "manifest.json"
    assert tool.bin_dirs == [Path("bin"), Path(".")]
    assert tool.env_add_path == []
    assert tool.get_all_required_paths() == [scoop_dir.joinpath(path) for path in ["apps/app1/1.0/bin", "apps/app1/1.0"]]

    tool = next(filter(lambda t: t.name == "app1" and t.version == "2.0", installed_tools))
    assert tool.name == "app1"
    assert tool.version == "2.0"
    assert tool.path == apps_dir.joinpath("app1/2.0")
    assert tool.manifest_file == tool.path / "manifest.json"
    assert tool.bin_dirs == [Path("app"), Path(".")]
    assert tool.env_add_path == []
    assert tool.get_all_required_paths() == [scoop_dir.joinpath(path) for path in ["apps/app1/2.0/app", "apps/app1/2.0"]]

    tool = next(filter(lambda t: t.name == "app2", installed_tools))
    assert tool.name == "app2"
    assert tool.version == "3.1.1"
    assert tool.path == apps_dir.joinpath("app2/3.1.1")
    assert tool.manifest_file == tool.path / "manifest.json"
    assert tool.bin_dirs == [Path(".")]
    assert tool.env_add_path == []
    assert tool.get_all_required_paths() == [scoop_dir.joinpath("apps/app2/3.1.1")]

    tool = next(filter(lambda t: t.name == "app3", installed_tools))
    assert tool.name == "app3"
    assert tool.version == "1.0"
    assert tool.path == apps_dir.joinpath("app3/1.0")
    assert tool.manifest_file == tool.path / "manifest.json"
    assert tool.bin_dirs == [Path("bin")]
    assert tool.env_add_path == [Path("bin")]
    assert tool.get_all_required_paths() == [scoop_dir.joinpath("apps/app3/1.0/bin")]


def test_install(scoop_dir: Path, tmp_path: Path) -> None:
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.exe")

    scoop_file = tmp_path / "scoopfile.json"
    scoop_file.write_text(
        """{
        "buckets": [],
        "apps": [
            {
                "Source": "versions",
                "Name": "app1"
            },
            {
                "Source": "main",
                "Name": "app2"
            }
        ]
    }"""
    )
    assert len(scoop_wrapper.install(scoop_file)) == 2


def test_scoop_file_parsing(tmp_path: Path) -> None:
    scoop_file = tmp_path / "scoopfile.json"
    scoop_file.write_text(
        """
    {
        "buckets": [
            {
                "Name": "main",
                "Source": "https://github.com/ScoopInstaller/main"
            },
            {
                "Name": "versions",
                "Source": "https://github.com/ScoopInstaller/Versions"
            }
        ],
        "apps": [
            {
                "Source": "versions",
                "Name": "python311"
            },
            {
                "Source": "main",
                "Name": "python"
            }
        ]
    }
    """
    )
    scoop_deps = ScoopInstallConfigFile.from_file(scoop_file)
    assert scoop_deps.bucket_names == ["main", "versions"]
    assert scoop_deps.app_names == ["python311", "python"]


@pytest.mark.parametrize(
    "required_apps, installed_apps, expected_app_versions, expected_exception",
    [
        (
            [ScoopFileElement(name="app1", source="test", version=None)],
            [
                InstalledScoopApp(
                    name="app1",
                    version="1.0.0",
                    path=Path("app1/1.0.0"),
                    manifest_file=Path("app1/1.0.0/manifest.json"),
                    bin_dirs=[],
                    env_add_path=[],
                ),
                InstalledScoopApp(
                    name="app1",
                    version="2.0.0",
                    path=Path("app1/2.0.0"),
                    manifest_file=Path("app1/2.0.0/manifest.json"),
                    bin_dirs=[],
                    env_add_path=[],
                ),
            ],
            ["2.0.0"],  # should pick latest
            None,
        ),
        (
            [ScoopFileElement(name="app2", source="test", version="1.0.0")],
            [
                InstalledScoopApp(
                    name="app2",
                    version="1.0.0",
                    path=Path("app2/1.0.0"),
                    manifest_file=Path("app2/1.0.0/manifest.json"),
                    bin_dirs=[],
                    env_add_path=[],
                )
            ],
            ["1.0.0"],  # exact match
            None,
        ),
        (
            [ScoopFileElement(name="app3", source="test", version="1.0.0")],
            [
                InstalledScoopApp(
                    name="app3",
                    version="2.0.0",
                    path=Path("app3/2.0.0"),
                    manifest_file=Path("app3/2.0.0/manifest.json"),
                    bin_dirs=[],
                    env_add_path=[],
                )
            ],
            [],
            UserNotificationException,  # version mismatch
        ),
        (
            [ScoopFileElement(name="app4", source="test", version=None)],
            [
                InstalledScoopApp(
                    name="app1",
                    version="1.0.0",
                    path=Path("app1/1.0.0"),
                    manifest_file=Path("app1/1.0.0/manifest.json"),
                    bin_dirs=[],
                    env_add_path=[],
                )
            ],
            [],
            UserNotificationException,  # app not installed
        ),
    ],
)
def test_map_required_apps_to_installed_apps(
    required_apps: list[ScoopFileElement],
    installed_apps: list[InstalledScoopApp],
    expected_app_versions: list[str],
    expected_exception: type[Exception] | None,
) -> None:
    if expected_exception:
        with pytest.raises(expected_exception):
            ScoopWrapper.map_required_apps_to_installed_apps(required_apps, installed_apps)
    else:
        result = ScoopWrapper.map_required_apps_to_installed_apps(required_apps, installed_apps)
        assert [r.version for r in result] == expected_app_versions


def test_do_install_missing(scoop_dir: Path) -> None:
    # Create a mock for scoop_install_config
    scoop_install_config = ScoopInstallConfigFile(
        buckets=[ScoopFileElement(name="bucket1", source="source1")],
        apps=[
            ScoopFileElement(name="app1", source="source1"),
            ScoopFileElement(name="app2", source="source2"),
        ],
    )

    app1, app2, app3 = (
        InstalledScoopApp(
            name=app_name,
            version="1.0",
            path=Path(f"/path/to/{app_name}"),
            manifest_file=Path(f"/path/to/{app_name}/manifest.json"),
            bin_dirs=[],
            env_add_path=[],
        )
        for app_name in ["app1", "app2", "app3"]
    )

    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.exe")

    with patch("py_app_dev.core.subprocess.SubprocessExecutor.execute", Mock()):
        assert len(scoop_wrapper.do_install_missing(scoop_install_config, [app1, app2])) == 0
        assert len(scoop_wrapper.do_install_missing(scoop_install_config, [app1])) == 1
        assert len(scoop_wrapper.do_install_missing(scoop_install_config, [app3])) == 2


@pytest.mark.skipif(sys.platform != "win32", reason="It requires powershell.")
def test_scoop_powershell_execution(tmp_path: Path) -> None:
    # Create a temporary powershell file to use Get-FileHash.
    ps_file = tmp_path / "test.ps1"
    ps_file.write_text(
        textwrap.dedent("""\
    Write-Host "PSHOME: $PSHOME"
    Write-Host "PSModulePath: $env:PSModulePath"
    # Get the hash of the script itself
    $hash = Get-FileHash -Path $MyInvocation.MyCommand.Path -Algorithm SHA256
    Write-Host $hash.Hash
    # Write hash to a file in the same directory
    $hash | ConvertTo-Json | Set-Content -Path $PSCommandPath.Replace(".ps1", ".hash")
    """)
    )
    ScoopWrapper.run_powershell_command(f"{ps_file.absolute()}", update_ps_module_path=True)
    assert (tmp_path / "test.hash").exists()


# Helper to create InstalledScoopApp list easily
def create_installed_list(apps: list[tuple[str, str]]) -> list[InstalledScoopApp]:
    return [
        InstalledScoopApp(
            name=name,
            version=ver,
            path=Path(f"/mock/{name}/{ver}"),
            manifest_file=Path(f"/mock/{name}/{ver}/manifest.json"),
            bin_dirs=[],
            env_add_path=[],
        )
        for name, ver in apps
    ]


# Helper to create ScoopFileElement list easily
def create_required_list(
    apps: list[tuple[str, str, str | None]],
) -> list[ScoopFileElement]:
    return [ScoopFileElement(name=name, source=src, version=ver) for name, src, ver in apps]


@pytest.mark.parametrize(
    "required_apps_data, installed_apps_data, expected_to_install_data",
    [
        # Case 1: No apps required, none installed -> Expect empty
        ([], [], []),
        # Case 2: Apps required, none installed -> Expect all required
        (
            [("git", "main", "2.40"), ("curl", "main", "8.0")],
            [],
            [("git", "main", "2.40"), ("curl", "main", "8.0")],
        ),
        # Case 3: All required (versioned) apps are installed -> Expect empty
        (
            [("git", "main", "2.40"), ("curl", "main", "8.0")],
            [("git", "2.40"), ("curl", "8.0")],
            [],
        ),
        # Case 4: Some required (versioned) apps installed, some not -> Expect missing
        (
            [
                ("git", "main", "2.40"),
                ("curl", "main", "8.0"),
                ("7zip", "main", "23.01"),
            ],
            [("git", "2.40"), ("7zip", "23.01")],
            [("curl", "main", "8.0")],
        ),
        # Case 5: Required app has version, installed has DIFFERENT version -> Expect required version
        (
            [("git", "main", "2.41")],
            [("git", "2.40")],
            [("git", "main", "2.41")],
        ),
        # Case 6: Required app has NO version, NO version installed -> Expect required (versionless)
        (
            [("git", "main", None)],
            [],
            [("git", "main", None)],
        ),
        # Case 7: Required app has NO version, SOME version installed -> Expect EMPTY (as one is already installed)
        (
            [("git", "main", None)],
            [("git", "2.40")],
            [],
        ),
        # Case 8: Mix of versioned/non-versioned requirements and installations
        (
            [
                ("git", "main", "2.41"),
                ("curl", "main", None),
                ("7zip", "main", "23.01"),
                ("nodejs", "main", None),
            ],
            [
                ("git", "2.40"),
                ("curl", "8.0"),
                ("nodejs", "18.17"),
            ],  # git wrong version, curl/nodejs installed, 7zip missing
            [
                ("git", "main", "2.41"),
                ("7zip", "main", "23.01"),
            ],  # Expect specific git, specific 7zip. Curl/Nodejs satisfied.
        ),
        # Case 9: Required app has version, multiple versions installed including required -> Expect empty
        (
            [("git", "main", "2.40")],
            [("git", "2.39"), ("git", "2.40"), ("git", "2.41")],
            [],
        ),
        # Case 10: Required app has version, multiple versions installed excluding required -> Expect required
        (
            [("git", "main", "2.42")],
            [("git", "2.39"), ("git", "2.40"), ("git", "2.41")],
            [("git", "main", "2.42")],
        ),
    ],
    ids=[
        "no_required_no_installed",
        "required_none_installed",
        "all_required_versioned_installed",
        "some_required_versioned_installed",
        "required_version_mismatch",
        "required_no_version_none_installed",
        "required_no_version_some_installed",
        "mixed_requirements_installations",
        "required_version_present_among_multiple",
        "required_version_missing_among_multiple",
    ],
)
def test_get_tools_to_be_installed(
    required_apps_data: list[tuple[str, str, str | None]],
    installed_apps_data: list[tuple[str, str]],
    expected_to_install_data: list[tuple[str, str, str | None]],
) -> None:
    """Tests the static method get_tools_to_be_installed with various scenarios."""
    required_apps = create_required_list(required_apps_data)
    installed_apps = create_installed_list(installed_apps_data)
    expected_to_install = create_required_list(expected_to_install_data)

    # Call the static method
    actual_to_install = ScoopWrapper.get_tools_to_be_installed(required_apps, installed_apps)

    # Compare sets for order independence, using the elements themselves (requires __eq__ and __hash__)
    assert set(actual_to_install) == set(expected_to_install)
    assert len(actual_to_install) == len(expected_to_install)  # Ensure counts match too


TEST_CASES: tuple[tuple[str, str, int], ...] = (
    ("1.0.0", "1.0.0", 0),
    ("1.2.3", "1-2-3", 0),
    ("1_0", "1.0", 0),
    ("1.01", "1.1", 0),
    ("1.007", "1.7", 0),
    # Major version
    ("2.0.0", "1.9.9", 1),
    ("1.0.0", "0.99.99", 1),
    ("0.99.99", "1.0.0", -1),
    # Minor version
    ("1.10.0", "1.9.5", 1),
    ("1.1.9", "1.2.0", -1),
    # Patch version
    ("1.1.3", "1.1.2", 1),
    ("1.1.2", "1.1.3", -1),
    # Handling non-numeric parts (treated as 0)
    ("1.2.1", "1.2.a", 1),  # 1 > 0
    ("1.2.beta", "1.2.alpha", 0),  # beta -> 0, alpha -> 0
    # --- Edge Cases ---
    ("", "", 0),  # Both empty
    ("1.0", "", 1),  # v1 present, v2 empty
    ("", "1.0", -1),  # v1 empty, v2 present
    ("a", "b", 0),  # Non-numeric treated as 0
    ("1a", "1b", 0),  # [1, 0] vs [1, 0]
    (
        "v1.2",
        "1.2",
        0,
    ),  # Leading non-numeric treated as 0 -> [0, 1, 2] vs [1, 2] -> this depends on regex. Correct parts: [1, 2] vs [1, 2]
    ("snapshot", "release", 0),  # Both map to [0]
)


@pytest.mark.parametrize("v1, v2, expected", TEST_CASES)
def test_semver_compare(v1: str, v2: str, expected: int) -> None:
    result = _semver_compare(v1, v2)
    assert result == expected, f"Comparison of '{v1}' and '{v2}' failed: Expected {expected}, Got {result}"


@pytest.mark.parametrize(
    "env_set, expected_env_vars",
    [
        ({"MY_COMP_ROOT": "$dir"}, {"MY_COMP_ROOT": "{path}"}),
        (
            {"MY_LIB": "my_lib", "MY_COMP_BIN": "$dir/bin"},
            {"MY_LIB": "my_lib", "MY_COMP_BIN": "{path}/bin"},
        ),
    ],
)
def test_env_vars_parsing(scoop_dir: Path, env_set: dict[str, Any], expected_env_vars: dict[str, Any]) -> None:
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.ps1")

    # Create a mock manifest file with env_set
    manifest_file = scoop_dir / "apps" / "app_with_env" / "1.0" / "manifest.json"
    manifest_file.parent.mkdir(parents=True)
    manifest_file.write_text(
        json.dumps(
            {
                "version": "1.0",
                "env_set": env_set,
            }
        )
    )

    # Parse the manifest file
    installed_app = scoop_wrapper.parse_manifest_file(manifest_file)

    # Format expected_env_vars with the actual path
    formatted_expected_env_vars = {key: value.format(path=str(installed_app.path)) for key, value in expected_env_vars.items()}

    # Assert the environment variables are correctly parsed
    assert installed_app.env_vars == formatted_expected_env_vars


def test_bin_dirs_with_root_executable(scoop_dir: Path) -> None:
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.ps1")

    # Create a mock manifest file with a root-level executable
    manifest_file = scoop_dir / "apps" / "app_with_root_exe" / "1.0" / "manifest.json"
    manifest_file.parent.mkdir(parents=True)
    manifest_file.write_text(
        json.dumps(
            {
                "version": "1.0",
                "bin": "ninja.exe",
            }
        )
    )

    # Parse the manifest file
    installed_app = scoop_wrapper.parse_manifest_file(manifest_file)

    # Assert the bin_dirs includes the app root directory
    assert installed_app.bin_dirs == [Path(".")], "The app root directory should be included in bin_dirs for root-level executables."


def test_parse_manifest_file_invalid_json(scoop_dir: Path) -> None:
    """Test that parse_manifest_file raises UserNotificationException for invalid JSON."""
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.ps1")

    # Create a mock manifest file with invalid JSON
    manifest_file = scoop_dir / "apps" / "app_with_invalid_json" / "1.0" / "manifest.json"
    manifest_file.parent.mkdir(parents=True)
    manifest_file.write_text("{ invalid json }")

    # Assert that UserNotificationException is raised with the correct message
    with pytest.raises(
        UserNotificationException,
        match=f"Failed to parse manifest file: {manifest_file.as_posix()}.*",
    ):
        scoop_wrapper.parse_manifest_file(manifest_file)


def test_parse_manifest_file_invalid_characters(scoop_dir: Path) -> None:
    """Test that parse_manifest_file raises UserNotificationException for invalid characters."""
    scoop_wrapper = create_scoop_wrapper(scoop_dir / "scoop.ps1")

    # Create a mock manifest file with invalid characters
    manifest_file = scoop_dir / "apps" / "app_with_invalid_chars" / "1.0" / "manifest.json"
    manifest_file.parent.mkdir(parents=True)
    manifest_file.write_text('\x00\x01\x02{"abc":"val"}')  # Invalid characters

    # Assert that UserNotificationException is raised with the correct message
    with pytest.raises(
        UserNotificationException,
        match=rf"Failed to parse manifest file: {manifest_file.as_posix()}.*",
    ):
        scoop_wrapper.parse_manifest_file(manifest_file)
