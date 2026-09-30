# Project CLI

The `aevox` command creates a C++23 web application with the same short
create/build/run workflow used by many higher-level frameworks. It works on
Linux and Windows with Python 3.10 or newer.

## Install

With pipx and Git installed, this
single command installs the CLI and places `aevox` on your command path:

```text
pipx install git+https://github.com/aevox-dev/Aevox.git@feat/aevox-cli
```

The command is the same in Bash, PowerShell, and Command Prompt. If pipx was
just installed, run `pipx ensurepath` once and open a new terminal. For a local
checkout, use `pipx install .` from the Aevox repository root.

The CLI itself only needs Python and Git. Native builds need CMake 3.27+, vcpkg,
and GCC 13+ with Ninja (Linux), or Visual Studio 2022 17.8+ with the C++
workload (Windows). Set `VCPKG_ROOT` to the root of a bootstrapped vcpkg clone.
`aevox doctor` reports missing tools and versions. Aevox does not support
macOS.

## First application

```text
aevox create hello_web
cd hello_web
aevox doctor
aevox run
```

Open <http://localhost:8080/>. `create` initializes Git, adds Aevox as a real
`vendor/aevox` submodule, stages the scaffold, and writes `.gitignore` and
`.dockerignore`. It does not make an initial commit. You can pin the dependency
with `--aevox-ref <tag-or-commit>` or use a different remote with `--aevox-url`.
After cloning an app, initialize its dependency with
`git submodule update --init --recursive`.

The starter has `src/` for C++ sources, `include/` for headers, `public/` for
static assets, `templates/` for page templates, `config/` for application
settings, and `cmake/` for the generated source manifest. The sample server
offers `/` and `/health`. The `public/` and `templates/` directories are a
conventional place for application files; wire your handlers or middleware to
them as the app grows.

The project root also contains `aevox.toml`. Edit it and restart the app to
change runtime settings and `[logging]` without recompiling. The starter calls
`App::create()` with that file and prints an error if it is missing or invalid.
`aevox run --config config/production.toml` selects another TOML file.
`AEVOX_CONFIG` can set the path when launching the executable directly.
Values explicitly set in TOML take precedence over `AEVOX_PORT` and
`AEVOX_HOST`; the default file leaves port and host commented out so
`aevox run --port 9090` works immediately.

## Commands

| Command | Action |
|---|---|
| `aevox create NAME [--path DIR]` | Create a project under `DIR` (current directory by default). The name becomes the CMake executable target. |
| `aevox doctor [--project DIR]` | Check CMake, Git, compiler, generator, vcpkg, and project submodule. |
| `aevox prepare [--project DIR]` | Recursively find C/C++ sources and headers in `src/` and `include/`, then refresh `cmake/AevoxSources.cmake`. |
| `aevox build [-p] [--release] [--jobs N]` | Configure with vcpkg and compile. `-p` runs `prepare` first. |
| `aevox run [--release] [--port N] [--host ADDRESS] [--config FILE] [--no-build]` | Prepare, build, and launch. `--no-build` runs an existing binary. |

Run these inside the project, or add `--project DIR` to `doctor`, `prepare`,
`build`, or `run`. Use `aevox run -- ARG...` to pass arguments to the native
executable. The starter reads `AEVOX_PORT`, `AEVOX_HOST`, and `AEVOX_CONFIG`;
`run --port`, `--host`, and `--config` set them for that process. Your own
`main.cpp` can keep or replace this convention. Log after `App` construction
or `App::create()`, because no writer is installed before an App exists.

`prepare` scans nested application CMake files for literal filenames already
assigned to custom targets. It records the remaining source and header files
in the generated manifest, so a new `src/features/users/handler.cpp` gets
compiled without hand-editing CMake. CMake expressions and computed filenames
cannot be interpreted statically; explicitly managed files remain under the
owner CMake file. Run `aevox build -p` after adding files, or use `aevox run`,
which prepares automatically. `aevox build` alone reuses the previous manifest.

## Docker

The starter includes a multi-stage Dockerfile. Initialize its Git submodule
before building the image:

```text
docker build -t hello_web .
docker run --rm -p 8080:8080 hello_web
```

The image installs GCC, CMake, Ninja, and vcpkg, builds the release target,
and runs the native executable on port 8080. Initial image builds take longer
because vcpkg compiles the framework dependencies. Change the mapped host
port with `-p 9090:8080`, or set the container port with `-e AEVOX_PORT=9090`
and map `-p 9090:9090`. The runtime image includes `aevox.toml` at `/app`;
you can mount another file there to change settings without rebuilding the image.
