"""Integration checks for the Git scaffold and recursive source preparation."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from aevox_cli.cli import main
from aevox_cli.prepare import prepare_project
from aevox_cli.scaffold import create_project


class ProjectCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        framework = self.root / "framework"
        framework.mkdir()
        (framework / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.27)\n", encoding="utf-8")
        (framework / "vcpkg.json").write_text('{"name": "aevox", "version": "0.1.0"}\n', encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(framework)], check=True)
        subprocess.run(["git", "-C", str(framework), "add", "."], check=True)
        subprocess.run(["git", "-C", str(framework), "-c", "user.name=Test",
                        "-c", "user.email=test@example.com", "commit", "-qm", "initial"], check=True)
        self.framework = framework

    def test_create_initializes_submodule_and_manifest(self) -> None:
        project = create_project("sample_app", self.root, str(self.framework))
        self.assertTrue((project / ".gitmodules").is_file())
        self.assertIn("vendor/aevox", (project / ".gitmodules").read_text(encoding="utf-8"))
        self.assertTrue((project / "vendor/aevox/vcpkg.json").is_file())
        self.assertTrue((project / "public/index.html").is_file())
        self.assertIn("src/main.cpp", (project / "cmake/AevoxSources.cmake").read_text(encoding="utf-8"))
        staged = subprocess.run(["git", "-C", str(project), "diff", "--cached", "--name-only"],
                                text=True, capture_output=True, check=True).stdout
        self.assertIn(".gitmodules", staged)
        self.assertIn("vendor/aevox", staged)

    def test_prepare_finds_nested_sources_and_respects_manual_cmake(self) -> None:
        project = create_project("sample_app", self.root, str(self.framework))
        feature = project / "src/features/users"
        feature.mkdir(parents=True)
        (feature / "handler.cpp").write_text("int handler() { return 1; }\n", encoding="utf-8")
        (feature / "handler.hpp").write_text("int handler();\n", encoding="utf-8")
        (feature / "manual.cpp").write_text("int manual() { return 2; }\n", encoding="utf-8")
        (feature / "CMakeLists.txt").write_text("add_library(custom manual.cpp)\n", encoding="utf-8")
        with (project / "src/CMakeLists.txt").open("a", encoding="utf-8") as cmake:
            cmake.write("\nadd_subdirectory(features/users)\n")
        paths = prepare_project(project)
        self.assertIn("src/features/users/handler.cpp", paths)
        self.assertIn("src/features/users/handler.hpp", paths)
        self.assertNotIn("src/features/users/manual.cpp", paths)
        manifest = (project / "cmake/AevoxSources.cmake").read_text(encoding="utf-8")
        self.assertEqual(paths, prepare_project(project))
        self.assertEqual(manifest, (project / "cmake/AevoxSources.cmake").read_text(encoding="utf-8"))

    def test_bad_name_does_not_create_project(self) -> None:
        self.assertEqual(main(["create", "bad-name", "--path", str(self.root),
                               "--aevox-url", str(self.framework)]), 1)
        self.assertFalse((self.root / "bad-name").exists())


if __name__ == "__main__":
    unittest.main()
