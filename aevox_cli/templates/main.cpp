#include <aevox/app.hpp>
#include <aevox/log.hpp>

#include <charconv>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

int main()
{
    aevox::AppConfig config;
    if (const char* value = std::getenv("AEVOX_PORT")) {
        unsigned int      port = 0;
        const std::string text{value};
        const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), port);
        if (error != std::errc{} || end != text.data() + text.size() || port == 0 || port > 65535) {
            std::cerr << "AEVOX_PORT must be between 1 and 65535\n";
            return 1;
        }
        config.port = static_cast<std::uint16_t>(port);
    }
    if (const char* value = std::getenv("AEVOX_HOST")) {
        config.host = value;
    }

    // aevox run sets the working directory to the project root, so the default
    // file is editable without rebuilding. AEVOX_CONFIG selects another file.
    std::string_view config_path{"aevox.toml"};
    if (const char* value = std::getenv("AEVOX_CONFIG")) {
        config_path = value;
    }
    auto created = aevox::App::create(config, config_path);
    if (!created) {
        const auto& error = created.error();
        std::cerr << "aevox config error (" << aevox::to_string(error.error_code())
                  << "): " << error.error_message() << '\n';
        return 1;
    }

    auto& app = *created;
    aevox::log::info("Starting {{PROJECT_NAME}} on {}:{}", app.config().host, app.config().port);
    app.get("/",
            [](aevox::Request&) { return aevox::Response::ok("Hello from {{PROJECT_NAME}}!\n"); });
    app.get("/health", [](aevox::Request&) { return aevox::Response::ok("ok\n"); });
    app.listen();
}
