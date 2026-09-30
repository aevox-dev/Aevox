"""The user-facing ``aevox`` command and toolchain checks."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .prepare import prepare_project
from .scaffold import AEVOX_URL, create_project


def _preset(release: bool) -> str:
    return f"{'windows' if os.name == 'nt' else 'linux'}-{'release' if release else 'debug'}"


def _tool_version(command: list[str], pattern: str) -> tuple[int, ...] | None:
    """Return numeric components from a tool's first matching version string."""
    if shutil.which(command[0]) is None:
        return None
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    match = re.search(pattern, result.stdout + result.stderr, re.IGNORECASE)
    return tuple(map(int, match.group(1).split("."))) if match else None


def doctor(project: Path) -> bool:
    """Report whether this host can build the framework from source."""
    checks: list[tuple[str, bool, str]] = []
    cmake = _tool_version(["cmake", "--version"], r"cmake version (\d+(?:\.\d+)+)")
    checks.append(("CMake >= 3.27", cmake is not None and cmake >= (3, 27),
                   ".".join(map(str, cmake)) if cmake else "install CMake"))
    git_path = shutil.which("git")
    checks.append(("Git", git_path is not None, git_path or "install Git for submodules"))
    if os.name == "nt":
        msvc = _tool_version(["cl"], r"Version (\d+(?:\.\d+)+)")
        checks.append(("MSVC 2022 >= 17.8", msvc is not None and msvc >= (19, 38),
                       ".".join(map(str, msvc)) if msvc else "use a VS 2022 Developer PowerShell"))
    elif sys.platform.startswith("linux"):
        gcc = _tool_version(["g++", "-dumpfullversion", "-dumpversion"], r"(\d+(?:\.\d+)+)")
        checks.append(("GCC >= 13", gcc is not None and gcc >= (13,),
                       ".".join(map(str, gcc)) if gcc else "install g++ 13 or newer"))
        ninja_path = shutil.which("ninja")
        checks.append(("Ninja", ninja_path is not None, ninja_path or "install ninja-build"))
    else:
        checks.append(("Supported OS", False, "Aevox supports Linux and Windows"))
    vcpkg = Path(os.environ.get("VCPKG_ROOT", "")) if os.environ.get("VCPKG_ROOT") else None
    checks.append(("VCPKG_ROOT", bool(vcpkg and (vcpkg / "scripts/buildsystems/vcpkg.cmake").is_file()),
                   str(vcpkg) if vcpkg else "set VCPKG_ROOT to your vcpkg checkout"))
    vcpkg_binary = vcpkg / ("vcpkg.exe" if os.name == "nt" else "vcpkg") if vcpkg else None
    checks.append(("vcpkg bootstrap", bool(vcpkg_binary and vcpkg_binary.is_file()),
                   str(vcpkg_binary) if vcpkg_binary else "bootstrap vcpkg first"))
    if (project / ".gitmodules").is_file() and (project / "src/CMakeLists.txt").is_file():
        submodule = project / "vendor/aevox/CMakeLists.txt"
        manifest = project / "vendor/aevox/vcpkg.json"
        sources = project / "cmake/AevoxSources.cmake"
        checks.append(("Aevox submodule", submodule.is_file(),
                       str(submodule) if submodule.is_file() else "run git submodule update --init --recursive"))
        checks.append(("vcpkg manifest", manifest.is_file(), str(manifest)))
        checks.append(("source manifest", sources.is_file(),
                       str(sources) if sources.is_file() else "run aevox prepare"))
    for label, good, detail in checks:
        print(f"{'OK' if good else 'FAIL':4}  {label}: {detail}")
    return all(good for _, good, _ in checks)


def build_project(project: Path, release: bool, prepare: bool, jobs: int | None) -> None:
    """Regenerate sources when requested, configure vcpkg, then compile."""
    if prepare:
        paths = prepare_project(project)
        print(f"Prepared {len(paths)} generated source entries", flush=True)
    preset = _preset(release)
    subprocess.run(["cmake", "--preset", preset], cwd=project, check=True)
    command = ["cmake", "--build", "--preset", preset]
    if jobs is not None:
        command.extend(["--parallel", str(jobs)])
    subprocess.run(command, cwd=project, check=True)


def run_project(project: Path, release: bool, build: bool, jobs: int | None,
                port: int | None, host: str | None, args: list[str]) -> int:
    """Build when needed and launch the native executable with passthrough args."""
    if build:
        build_project(project, release, prepare=True, jobs=jobs)
    config = "Release" if release else "Debug"
    binary = (project / "build" / _preset(release) / "src" /
              (config if os.name == "nt" else "") /
              (project.name + (".exe" if os.name == "nt" else "")))
    if not binary.is_file():
        raise FileNotFoundError(f"{binary} is missing; run aevox build -p")
    env = os.environ.copy()
    if port is not None:
        env["AEVOX_PORT"] = str(port)
    if host is not None:
        env["AEVOX_HOST"] = host
    return subprocess.run([str(binary), *args], cwd=project, env=env, check=False).returncode


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aevox", description="Manage an Aevox C++ web app")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="scaffold and initialize a Git project")
    create.add_argument("name", help="project directory and CMake target name")
    create.add_argument("--path", type=Path, default=Path.cwd(), help="parent directory")
    create.add_argument("--aevox-url", default=AEVOX_URL, help="framework Git URL")
    create.add_argument("--aevox-ref", help="framework branch, tag, or commit")

    for name in ("doctor", "prepare", "build", "run"):
        command = commands.add_parser(name, help={
            "doctor": "check the compiler and build prerequisites",
            "prepare": "register application sources in CMake recursively",
            "build": "configure and compile the application",
            "run": "build and start the application",
        }[name])
        command.add_argument("--project", type=Path, default=Path.cwd(), help="application directory")
        if name in ("build", "run"):
            command.add_argument("--release", action="store_true", help="use the release preset")
            command.add_argument("--jobs", type=int, help="maximum parallel build jobs")
        if name == "build":
            command.add_argument("-p", "--prepare", action="store_true", help="run prepare before building")
        if name == "run":
            command.add_argument("--no-build", action="store_true", help="run an existing binary")
            command.add_argument("--port", type=int, choices=range(1, 65536), metavar="PORT")
            command.add_argument("--host", help="bind address")
            command.add_argument("args", nargs=argparse.REMAINDER, help="arguments after -- passed to the app")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            project = create_project(args.name, args.path, args.aevox_url, args.aevox_ref)
            print(f"Created {project}\nNext: cd {project} && aevox doctor && aevox run")
        elif args.command == "doctor":
            return 0 if doctor(args.project.resolve()) else 1
        elif args.command == "prepare":
            paths = prepare_project(args.project.resolve())
            print(f"Prepared {len(paths)} generated source entries")
        elif args.command == "build":
            if args.jobs is not None and args.jobs < 1:
                raise ValueError("--jobs must be positive")
            build_project(args.project.resolve(), args.release, args.prepare, args.jobs)
        elif args.command == "run":
            if args.jobs is not None and args.jobs < 1:
                raise ValueError("--jobs must be positive")
            passed = args.args[1:] if args.args[:1] == ["--"] else args.args
            return run_project(args.project.resolve(), args.release, not args.no_build,
                               args.jobs, args.port, args.host, passed)
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as error:
        print(f"aevox: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"aevox: command failed with exit status {error.returncode}: {' '.join(map(str, error.cmd))}",
              file=sys.stderr)
        return error.returncode or 1
    except KeyboardInterrupt:
        return 130
    return 0
