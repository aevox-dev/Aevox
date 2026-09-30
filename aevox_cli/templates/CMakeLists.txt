cmake_minimum_required(VERSION 3.27)
project({{PROJECT_NAME}} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Aevox is a real Git submodule. Its tests and examples are built only when
# Aevox itself is the top-level project.
add_subdirectory(vendor/aevox)
add_subdirectory(src)
