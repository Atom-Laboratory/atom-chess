#pragma once

#include <filesystem>
#include <string>

namespace utils
{
    std::filesystem::path executablePath();

    std::filesystem::path assetPath(const std::string& relativePath);
}