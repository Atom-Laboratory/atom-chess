#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "motion::motion" for configuration ""
set_property(TARGET motion::motion APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(motion::motion PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libmotion.so"
  IMPORTED_SONAME_NOCONFIG "libmotion.so"
  )

list(APPEND _cmake_import_check_targets motion::motion )
list(APPEND _cmake_import_check_files_for_motion::motion "${_IMPORT_PREFIX}/lib/libmotion.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
