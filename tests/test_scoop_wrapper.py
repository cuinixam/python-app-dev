import json
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.scoop_wrapper import (
    InstalledScoopApp,
    ScoopFileElement,
    ScoopInstallConfigFile,
    ScoopWrapper,
)


def create_scoop_wrapper(scoop_executable: Optional[Path]) -> ScoopWrapper:
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
    tool1 = next(filter(lambda t: t.name == "app1" and t.version == "1.0", installed_tools))
    assert tool1.name == "app1"
    assert tool1.version == "1.0"
    assert tool1.path == apps_dir.joinpath("app1/1.0")
    assert tool1.manifest_file == tool1.path / "manifest.json"
    assert tool1.bin_dirs == [Path("bin")]
    assert tool1.env_add_path == []

    tool2 = next(filter(lambda t: t.name == "app1" and t.version == "2.0", installed_tools))
    assert tool2.name == "app1"
    assert tool2.version == "2.0"
    assert tool2.path == apps_dir.joinpath("app1/2.0")
    assert tool2.manifest_file == tool2.path / "manifest.json"
    assert tool2.bin_dirs == [Path("app")]
    assert tool2.env_add_path == []

    tool3 = next(filter(lambda t: t.name == "app2", installed_tools))
    assert tool3.name == "app2"
    assert tool3.version == "3.1.1"
    assert tool3.path == apps_dir.joinpath("app2/3.1.1")
    assert tool3.manifest_file == tool3.path / "manifest.json"
    assert tool3.bin_dirs == []
    assert tool3.env_add_path == []

    tool4 = next(filter(lambda t: t.name == "app3", installed_tools))
    assert tool4.name == "app3"
    assert tool4.version == "1.0"
    assert tool4.path == apps_dir.joinpath("app3/1.0")
    assert tool4.manifest_file == tool4.path / "manifest.json"
    assert tool4.bin_dirs == [Path("bin")]
    assert tool4.env_add_path == [Path("bin")]
    assert len(tool4.get_all_required_paths()) == 2  # install path and bin


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


def test_map_required_apps_to_installed_apps():
    # Define installed apps
    installed_apps = [
        InstalledScoopApp(
            "app1",
            "1.0",
            Path("/path/to/app1"),
            [],
            [],
            Path("/path/to/app1/manifest.json"),
        ),
        InstalledScoopApp(
            "app2",
            "1.0",
            Path("/path/to/app2"),
            [],
            [],
            Path("/path/to/app2/manifest.json"),
        ),
    ]

    # Test Case 1: All required apps are installed
    app_names = ["app1", "app2"]
    assert ScoopWrapper.map_required_apps_to_installed_apps(app_names, installed_apps) == installed_apps

    # Test Case 2: Some required apps are not installed
    app_names = ["app1", "app3"]
    with pytest.raises(UserNotificationException) as e:
        ScoopWrapper.map_required_apps_to_installed_apps(app_names, installed_apps)
    assert str(e.value) == "Could not find 'app3' in the installed apps. Something went wrong during the scoop installation."

    # Test Case 3: No required apps are installed
    app_names = ["app3", "app4"]
    with pytest.raises(UserNotificationException):
        ScoopWrapper.map_required_apps_to_installed_apps(app_names, installed_apps)


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
