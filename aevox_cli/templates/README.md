# {{PROJECT_NAME}}

Aevox C++23 web application.

```bash
aevox doctor
aevox run
```

The server listens on port 8080. Visit `http://localhost:8080/` or
`http://localhost:8080/health`. Run `aevox run --port 9090` to change it.
Edit `aevox.toml` in this directory to configure the server and its logger,
then restart the app; no rebuild is needed. `aevox run --config path/to/other.toml`
selects another file. TOML values take precedence over `AEVOX_PORT` and
`AEVOX_HOST` when those keys are present in the file.

Put C++ sources under `src/`, headers under `include/`, static files under
`public/`, templates under `templates/`, and configuration under `config/`.
After adding a source, run `aevox build -p` or `aevox run`; both refresh
`cmake/AevoxSources.cmake` recursively. Regular `aevox build` reuses it.
Call `aevox::log::info(...)` after constructing `App` or after `App::create()`;
messages sent before an `App` exists have no configured writer.

The Aevox dependency is pinned as `vendor/aevox`, a Git submodule. After
cloning this app, run `git submodule update --init --recursive`.

```bash
docker build -t {{PROJECT_NAME}} .
docker run --rm -p 8080:8080 {{PROJECT_NAME}}
```

Set `VCPKG_ROOT` to a vcpkg checkout for local builds. Docker installs its
own toolchain. The first build downloads and compiles Aevox dependencies.
