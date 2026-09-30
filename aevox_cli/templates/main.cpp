#include <aevox/app.hpp>

#include <charconv>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

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

    aevox::App app{config};
    app.get("/",
            [](aevox::Request&) { return aevox::Response::ok("Hello from {{PROJECT_NAME}}!\n"); });
    app.get("/health", [](aevox::Request&) { return aevox::Response::ok("ok\n"); });
    app.listen();
}
