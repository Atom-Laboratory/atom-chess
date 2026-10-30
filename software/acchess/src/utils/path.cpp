#include "utils/path.hpp"

namespace utils
{

std::filesystem::path executablePath()
{
    return std::filesystem::canonical("/proc/self/exe").parent_path();
}

std::filesystem::path assetPath(const std::string& relativePath)
{
    return executablePath() / "assets" / relativePath;
}

}