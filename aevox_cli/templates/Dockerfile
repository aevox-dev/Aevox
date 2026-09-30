# Build with the same GCC/CMake/vcpkg toolchain as a Linux host.
FROM ubuntu:24.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive VCPKG_ROOT=/opt/vcpkg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates cmake curl g++-13 gcc-13 git ninja-build pkg-config \
    python3 tar unzip zip && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/microsoft/vcpkg.git "$VCPKG_ROOT" && \
    "$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics
ENV CC=gcc-13 CXX=g++-13
WORKDIR /app
COPY . .
# The submodule directory must be populated before docker build.
RUN test -f vendor/aevox/CMakeLists.txt
RUN cmake --preset linux-release -DCMAKE_CXX_COMPILER=g++-13 && \
    cmake --build --preset linux-release --parallel 2

FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/build/linux-release/src/{{PROJECT_NAME}} /usr/local/bin/{{PROJECT_NAME}}
COPY --from=builder /app/aevox.toml /app/aevox.toml
ENV AEVOX_HOST=0.0.0.0 AEVOX_PORT=8080
EXPOSE 8080
CMD ["/usr/local/bin/{{PROJECT_NAME}}"]
