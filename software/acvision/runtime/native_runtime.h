#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#define ACVISION_API __declspec(dllexport)
#else
#define ACVISION_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t abi_version;
    int32_t board_valid;
    int32_t oriented;
    int32_t has_foreground;
    double homography[9];
    double reference_residual;
    int32_t candidates[64];
    int32_t center_valid[64];
    double centers[128];
} AcVisionFrame;

ACVISION_API uint32_t acvision_runtime_version(void);
ACVISION_API size_t acvision_frame_size(void);
ACVISION_API const char* acvision_runtime_source(void);
ACVISION_API const char* acvision_runtime_error(void);
ACVISION_API void* acvision_runtime_create(const char* layout_path);
ACVISION_API void acvision_runtime_destroy(void* context);
ACVISION_API int acvision_runtime_empty(void* context, const uint8_t* rgb,
                                       size_t bytes, int width, int height);
ACVISION_API int acvision_runtime_process(void* context, const uint8_t* rgb,
                                         size_t bytes, int width, int height,
                                         AcVisionFrame* result, uint8_t* rectified_rgb,
                                         size_t output_bytes);
#ifdef __cplusplus
}
#endif
