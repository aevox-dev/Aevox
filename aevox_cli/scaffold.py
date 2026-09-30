"""Create an application from the files shipped with the CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

from .prepare import prepare_project

AEVOX_URL = "https://github.com/aevox-dev/Aevox.git"
TEMPLATES = files("aevox_cli").joinpath("templates")
PROJECT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
RESERVED_NAMES = {
    "all", "clean", "help", "install", "test", "aevox_core", "aevox_http", "aevox_router",
    "con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def create_project(name: str, parent: Path, aevox_url: str = AEVOX_URL,
                   aevox_ref: str | None = None) -> Path:
    """Create a new Git repository; remove it if a setup command fails.

    ``name`` doubles as the CMake target, so it uses portable CMake identifier
    characters. The Aevox dependency is recorded as a real Git submodule.
    """
    if not PROJECT_NAME.fullmatch(name) or name.lower() in RESERVED_NAMES:
        raise ValueError("project name must start with a letter, use only letters, digits, or _, and not be a CMake target name")
    project = (parent / name).resolve()
    if project.exists():
        raise FileExistsError(f"{project} already exists")
    project.mkdir(parents=True)
    try:
        for directory in ("src", "include", "public", "templates", "config", "cmake"):
            (project / directory).mkdir()
        for source, target in (
            ("CMakeLists.txt", "CMakeLists.txt"),
            ("CMakePresets.json", "CMakePresets.json"),
            ("src.CMakeLists.txt", "src/CMakeLists.txt"),
            ("main.cpp", "src/main.cpp"),
            ("aevox.toml", "aevox.toml"),
            ("gitignore", ".gitignore"),
            ("dockerignore", ".dockerignore"),
            ("Dockerfile", "Dockerfile"),
            ("README.md", "README.md"),
        ):
            content = TEMPLATES.joinpath(source).read_text(encoding="utf-8")
            (project / target).write_text(content.replace("{{PROJECT_NAME}}", name), encoding="utf-8")
        (project / "public/index.html").write_text(
            f"<!doctype html><html lang=\"en\"><title>{name}</title><h1>{name}</h1></html>\n",
            encoding="utf-8",
        )
        (project / "config/.gitkeep").touch()
        (project / "templates/.gitkeep").touch()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        # Allow a local path for offline development and integration testing.
        subprocess.run(
            ["git", "-c", "protocol.file.allow=always", "-C", str(project),
             "submodule", "add", "-q", aevox_url, "vendor/aevox"],
            check=True,
        )
        if aevox_ref:
            subprocess.run(["git", "-C", str(project / "vendor/aevox"),
                            "checkout", aevox_ref], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "-C", str(project), "add", "vendor/aevox"], check=True)
        # The submodule contains the dependency manifest and its pinned baseline.
        manifest = project / "vendor/aevox/vcpkg.json"
        if not manifest.is_file() or json.loads(manifest.read_text(encoding="utf-8")).get("name") != "aevox":
            raise ValueError("the Aevox submodule has no valid vcpkg manifest")
        prepare_project(project)
        subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    except (OSError, subprocess.CalledProcessError, ValueError):
        shutil.rmtree(project)
        raise
    return project
