import platform
from pathlib import Path
from textwrap import dedent

import pytest

from py_app_dev.core.env_setup_scripts import (
    BatEnvSetupScriptGenerator,
    Ps1EnvSetupScriptGenerator,
    ShEnvSetupScriptGenerator,
)
from py_app_dev.core.subprocess import SubprocessExecutor


@pytest.fixture
def sample_environment() -> dict[str, str]:
    return {"VAR1": "value1", "VAR2": "value2 with spaces"}


@pytest.fixture
def sample_install_dirs(tmp_path: Path) -> list[Path]:
    dir_a = tmp_path / "dirA"
    dir_b = tmp_path / "dirB"
    dir_a.mkdir()
    dir_b.mkdir()
    return [dir_a, dir_b]


def test_bat_setup_script(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    output_file = tmp_path / "setup_env.bat"
    generator = BatEnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=output_file,
    )

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
def test_bat_setup_script_integration(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    bat_script = tmp_path / "setup_env.bat"
    gen = BatEnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=bat_script,
    )
    gen.to_file()

    # Create the runner script that calls the generated .bat script
    runner_bat = tmp_path / "runner.bat"
    runner_bat.write_text(f"@echo off\ncall {bat_script}\necho VAR1=%VAR1%\necho VAR2=%VAR2%\necho PATH=%PATH%\n")

    process = SubprocessExecutor(["cmd.exe", "/c", str(runner_bat)], capture_output=True, print_output=False).execute(handle_errors=False)

    assert process and process.returncode == 0
    assert "VAR1=value1" in process.stdout
    assert f"PATH={tmp_path.joinpath('dirA')}" in process.stdout


def test_ps1_setup_script(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    output_file = tmp_path / "setup_env.ps1"
    generator = Ps1EnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=output_file,
    )

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
def test_ps1_setup_script_integration(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    ps1_script = tmp_path / "setup_env.ps1"
    gen = Ps1EnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=ps1_script,
    )
    gen.to_file()

    runner_ps1 = tmp_path / "runner.ps1"
    runner_ps1.write_text(f'. .\\{ps1_script.name}\nWrite-Host "VAR1=$env:VAR1"\nWrite-Host "VAR2=$env:VAR2"\nWrite-Host "PATH=$env:PATH"\n')

    process = SubprocessExecutor(
        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(runner_ps1)],
        capture_output=True,
        print_output=False,
        cwd=tmp_path,
    ).execute(handle_errors=False)

    assert process and process.returncode == 0
    assert "VAR1=value1" in process.stdout
    assert f"PATH={tmp_path.joinpath('dirA')}" in process.stdout


def test_sh_setup_script(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    output_file = tmp_path / "setup_env.sh"
    generator = ShEnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=output_file,
    )

    generator.to_file()
    content = output_file.read_text("utf-8")

    path_parts = ":".join(str(d) for d in sample_install_dirs)
    expected = dedent(f"""\
        #!/bin/bash
        export VAR1='value1'
        export VAR2='value2 with spaces'
        export PATH='{path_parts}':"$PATH"
        """)
    assert content == expected


@pytest.mark.skipif(platform.system().lower() == "windows", reason="Requires Unix-like system")
def test_sh_setup_script_integration(tmp_path: Path, sample_environment: dict[str, str], sample_install_dirs: list[Path]) -> None:
    sh_script = tmp_path / "setup_env.sh"
    gen = ShEnvSetupScriptGenerator(
        install_dirs=sample_install_dirs,
        environment=sample_environment,
        output_file=sh_script,
    )
    gen.to_file()

    # Make the script executable
    sh_script.chmod(0o755)

    # Create a runner script that sources the generated script and prints the variables
    runner_sh = tmp_path / "runner.sh"
    runner_sh.write_text(f'#!/bin/bash\nsource {sh_script}\necho "VAR1=$VAR1"\necho "VAR2=$VAR2"\necho "PATH=$PATH"\n')
    runner_sh.chmod(0o755)

    process = SubprocessExecutor([str(runner_sh)], capture_output=True, print_output=False, cwd=tmp_path).execute(handle_errors=False)

    assert process and process.returncode == 0
    assert "VAR1=value1" in process.stdout
    assert "VAR2=value2 with spaces" in process.stdout
    assert f"{tmp_path.joinpath('dirA')}" in process.stdout
    assert f"{tmp_path.joinpath('dirB')}" in process.stdout
