#include "native_runtime.h"
#include "../apps/perception_offline.hpp"
#include "piece_location/piece_location.hpp"
#include <algorithm>
#include <cstring>
#include <memory>

namespace {
thread_local std::string error;
constexpr size_t outputBytes = 800 * 800 * 3;
struct Context {
    std::optional<ac::BoardReference> reference;
    cv::Mat empty;
    cv::Size emptySize;
};

cv::Mat decode(const uint8_t* rgb, size_t bytes, int width, int height)
{
    if (!rgb || width < 27 || height < 27 || width > 8192 || height > 8192 ||
        bytes != static_cast<size_t>(width) * height * 3)
        throw std::invalid_argument("INVALID_RGB_BUFFER");
    cv::Mat input(height, width, CV_8UC3, const_cast<uint8_t*>(rgb));
    cv::Mat bgr;
    cv::cvtColor(input, bgr, cv::COLOR_RGB2BGR);
    return bgr;
}

ac::offline::Result process(Context& context, const cv::Mat& bgr)
{
    return ac::offline::process(bgr, context.reference ? &*context.reference : nullptr);
}
}

extern "C" {
uint32_t acvision_runtime_version(void) { return 1; }
size_t acvision_frame_size(void) { return sizeof(AcVisionFrame); }
const char* acvision_runtime_source(void) { return ACVISION_SOURCE_SHA256; }
const char* acvision_runtime_error(void) { return error.c_str(); }

void* acvision_runtime_create(const char* layout_path)
{
    error.clear();
    try {
        auto context = std::make_unique<Context>();
        if (layout_path && layout_path[0]) context->reference = ac::loadBoardReference(layout_path);
        return context.release();
    } catch (const std::exception& exception) {
        error = exception.what();
        return nullptr;
    }
}

void acvision_runtime_destroy(void* context) { delete static_cast<Context*>(context); }

int acvision_runtime_empty(void* pointer, const uint8_t* rgb, size_t bytes, int width, int height)
{
    error.clear();
    if (!pointer) { error = "CLOSED_CONTEXT"; return -1; }
    auto& context = *static_cast<Context*>(pointer);
    context.empty.release();
    context.emptySize = {};
    try {
        const auto bgr = decode(rgb, bytes, width, height);
        const auto result = process(context, bgr);
        if (!result.referenceOriented || !result.observation) {
            error = "EMPTY_REFERENCE_UNAVAILABLE";
            return 0;
        }
        context.empty = result.rectified.clone();
        context.emptySize = bgr.size();
        return 1;
    } catch (const std::exception& exception) {
        error = exception.what();
        return -1;
    }
}

int acvision_runtime_process(void* pointer, const uint8_t* rgb, size_t bytes,
                            int width, int height, AcVisionFrame* output,
                            uint8_t* rectified_rgb, size_t output_bytes)
{
    error.clear();
    if (output) {
        *output = {};
        output->abi_version = 1;
        std::fill(std::begin(output->candidates), std::end(output->candidates), -1);
    }
    if (rectified_rgb && output_bytes == outputBytes)
        std::memset(rectified_rgb, 0, outputBytes);
    try {
        if (!pointer || !output || !rectified_rgb || output_bytes != outputBytes)
            throw std::invalid_argument("INVALID_CONTEXT_OR_OUTPUT");
        auto& context = *static_cast<Context*>(pointer);
        const auto bgr = decode(rgb, bytes, width, height);
        const auto result = process(context, bgr);
        if (!result.observation) return 0;

        output->board_valid = 1;
        output->oriented = result.referenceOriented ? 1 : 0;
        output->reference_residual = result.referenceResidual;
        std::memcpy(output->homography, result.homography.ptr<double>(), 9*sizeof(double));
        cv::Mat rectified;
        cv::cvtColor(result.rectified, rectified, cv::COLOR_BGR2RGB);
        std::memcpy(rectified_rgb, rectified.data, outputBytes);
        for (int row = 0; row < 8; ++row)
            for (int col = 0; col < 8; ++col)
                output->candidates[row*8+col] = static_cast<int>(result.observation->cells[row][col]);

        if (!context.empty.empty() && context.emptySize == bgr.size() && result.referenceOriented) {
            const auto centers = ac::locateForeground(result.rectified, context.empty);
            output->has_foreground = 1;
            for (int row = 0; row < 8; ++row) for (int col = 0; col < 8; ++col) {
                const auto& center = centers[row][col];
                if (center) {
                    const int index = row*8+col;
                    output->center_valid[index] = 1;
                    output->centers[index*2] = center->x;
                    output->centers[index*2+1] = center->y;
                }
            }
        }
        return 0;
    } catch (const std::exception& exception) {
        error = exception.what();
        if (output) {
            *output = {};
            output->abi_version = 1;
            std::fill(std::begin(output->candidates), std::end(output->candidates), -1);
        }
        return -1;
    }
}
}
