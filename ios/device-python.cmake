# Explicit cross-Python contract: a macOS executable and an iPhone framework.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "iOS" OR BUILD_SHARED_LIBS)
  message(FATAL_ERROR "The device Python override requires static iOS modules")
endif()
foreach(path "${TT_HOST_PYTHON}" "${TT_IOS_PYTHON_FRAMEWORK}/Headers/Python.h"
             "${TT_IOS_PYTHON_FRAMEWORK}/Python")
  if(NOT EXISTS "${path}")
    message(FATAL_ERROR "Missing pinned Python build output: ${path}")
  endif()
endforeach()
execute_process(COMMAND "${TT_HOST_PYTHON}" -c "import platform; print(platform.python_version())"
  OUTPUT_VARIABLE Python_VERSION OUTPUT_STRIP_TRAILING_WHITESPACE
  COMMAND_ERROR_IS_FATAL ANY)
if(NOT Python_VERSION STREQUAL "3.13.9")
  message(FATAL_ERROR "The host interpreter must match the pinned device Python")
endif()
set(Python_FOUND TRUE)
set(Python_EXECUTABLE "${TT_HOST_PYTHON}")
set(Python_INCLUDE_DIRS "${TT_IOS_PYTHON_FRAMEWORK}/Headers")
set(Python_LIBRARY_DIRS "${TT_IOS_PYTHON_FRAMEWORK}")
add_library(Python::Module INTERFACE IMPORTED GLOBAL)
set_target_properties(Python::Module PROPERTIES
  INTERFACE_INCLUDE_DIRECTORIES "${Python_INCLUDE_DIRS}"
  INTERFACE_LINK_LIBRARIES "${TT_IOS_PYTHON_FRAMEWORK}/Python")
# These archives will be registered as built-in modules by the native host.
# Do not derive target install paths or extension names from macOS sysconfig.
set(PYTHON_LIB_INSTALL_DIR "lib/python3.13" CACHE STRING "" FORCE)
set(PYTHON_ARCH_INSTALL_DIR "lib/python3.13" CACHE STRING "" FORCE)
set(PYTHON_EXTENSION_SUFFIX ".a" CACHE STRING "" FORCE)
