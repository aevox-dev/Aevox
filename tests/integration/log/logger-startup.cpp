// The App-owned logger must accept messages before listen() starts.

#include <aevox/app.hpp>
#include <aevox/log.hpp>

#include <catch2/catch_test_macros.hpp>

#include <chrono>
#include <filesystem>
#include <format>
#include <fstream>
#include <iterator>
#include <string>

TEST_CASE("Log - App startup message is written before listen", "[integration][log]")
{
    const auto path = std::filesystem::temp_directory_path() /
                      std::format("aevox-startup-{}.log",
                                  std::chrono::steady_clock::now().time_since_epoch().count());
    {
        aevox::AppConfig config;
        config.logging.destination = aevox::LogDestination::File;
        config.logging.file_path   = path.string();

        // App::create moves a temporary App into expected. Its moved-from
        // destructor must leave the installed writer alone.
        auto created = aevox::App::create(config);
        REQUIRE(created.has_value());

        aevox::log::info("startup message");
        REQUIRE(aevox::log::flush().has_value());

        std::ifstream     file{path};
        const std::string content{std::istreambuf_iterator<char>{file},
                                  std::istreambuf_iterator<char>{}};
        CHECK(content.find("startup message") != std::string::npos);
    }
    CHECK(std::filesystem::remove(path));
}
