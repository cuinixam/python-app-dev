import platform
from pathlib import Path
from textwrap import dedent
from typing import Dict, List

import pytest

from py_app_dev.core.env_setup_scripts import BatEnvSetupScriptGenerator, Ps1EnvSetupScriptGenerator
from py_app_dev.core.subprocess import SubprocessExecutor


@pytest.fixture
def sample_environment() -> Dict[str, str]:
    return {"VAR1": "value1", "VAR2": "value2 with spaces"}


@pytest.fixture
def sample_install_dirs(tmp_path: Path) -> List[Path]:
    dir_a = tmp_path / "dirA"
    dir_b = tmp_path / "dirB"
    dir_a.mkdir()
    dir_b.mkdir()
    return [dir_a, dir_b]


def test_bat_setup_script(tmp_path: Path, sample_environment: Dict[str, str], sample_install_dirs: List[Path]) -> None:
    output_file = tmp_path / "setup_env.bat"
    generator = BatEnvSetupScriptGenerator(install_dirs=sample_install_dirs, environment=sample_environment, output_file=output_file)

    generator.to_file()
    content = output_file.read_text("utf-8")

    path_parts = ";".join(str(d) for d in sample_install_dirs)
    expected = dedent(f"""\
        @echo off
        set "VAR1=value1"
        set "VAR2=value2 with spaces"
        set "PATH={path_parts};%PATH%"
        """)
    assert content == expected


@pytest.mark.skipif(platform.system().lower() != "windows", reason="Requires Windows")
def test_bat_setup_script_integration(tmp_path: Path, sample_environment: Dict[str, str], sample_install_dirs: List[Path]) -> None:
    bat_script = tmp_path / "setup_env.bat"
    gen = BatEnvSetupScriptGenerator(install_dirs=sample_install_dirs, environment=sample_environment, output_file=bat_script)
    gen.to_file()

    # Create the runner script that calls the generated .bat script
    runner_bat = tmp_path / "runner.bat"
    runner_bat.write_text("@echo off\n" f"call {bat_script}\n" "echo VAR1=%VAR1%\n" "echo VAR2=%VAR2%\n" "echo PATH=%PATH%\n")

    process = SubprocessExecutor(["cmd.exe", "/c", str(runner_bat)], capture_output=True, print_output=False).execute(handle_errors=False)

    assert process and process.returncode == 0
    assert "VAR1=value1" in process.stdout
    assert f"PATH={tmp_path.joinpath('dirA')}" in process.stdout


def test_ps1_setup_script(tmp_path: Path, sample_environment: Dict[str, str], sample_install_dirs: List[Path]) -> None:
    output_file = tmp_path / "setup_env.ps1"
    generator = Ps1EnvSetupScriptGenerator(install_dirs=sample_install_dirs, environment=sample_environment, output_file=output_file)

    generator.to_file()
    content = output_file.read_text("utf-8")

    path_parts = ";".join(str(d) for d in sample_install_dirs)
    expected = dedent(f"""\
        $env:VAR1="value1"
        $env:VAR2="value2 with spaces"
        $newPaths = "{path_parts}"
        $env:PATH = $newPaths + [System.IO.Path]::PathSeparator + $env:PATH
    """)
    assert content == expected


@pytest.mark.skipif(platform.system().lower() != "windows", reason="Requires Windows")
def test_ps1_setup_script_integration(tmp_path: Path, sample_environment: Dict[str, str], sample_install_dirs: List[Path]) -> None:
    ps1_script = tmp_path / "setup_env.ps1"
    gen = Ps1EnvSetupScriptGenerator(install_dirs=sample_install_dirs, environment=sample_environment, output_file=ps1_script)
    gen.to_file()

    runner_ps1 = tmp_path / "runner.ps1"
    runner_ps1.write_text(f". .\\{ps1_script.name}\n" 'Write-Host "VAR1=$env:VAR1"\n' 'Write-Host "VAR2=$env:VAR2"\n' 'Write-Host "PATH=$env:PATH"\n')

    process = SubprocessExecutor(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(runner_ps1)], capture_output=True, print_output=False, cwd=tmp_path).execute(
        handle_errors=False
    )

    assert process and process.returncode == 0
    assert "VAR1=value1" in process.stdout
    assert f"PATH={tmp_path.joinpath('dirA')}" in process.stdout
