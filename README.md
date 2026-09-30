# Aevox

[![CI](https://github.com/MohammadMokhalled/Aevox/actions/workflows/main.yml/badge.svg)](https://github.com/MohammadMokhalled/Aevox/actions/workflows/main.yml)

A high-performance C++23 web framework targeting 1M+ HTTP/1.1 requests/second on commodity hardware.

> [!NOTE]  
> This is an experimental project for me to see how far I could go with AI and test different methods of using AI to generate code. So it is not something to be considered as stable, working, or fully human involved, maybe some day it will become one. 

## Create an application

Install the Python CLI with `pipx install git+https://github.com/aevox-dev/Aevox.git@feat/aevox-cli`
on Linux or Windows. Then run:

```text
aevox create hello_web
cd hello_web
aevox doctor
aevox run
```

Set `VCPKG_ROOT` to a bootstrapped vcpkg checkout for local builds. See the
[CLI guide](docs/guide/cli.md) for compiler requirements, Docker, and command options.
