# Included at the end of the pinned Panda root CMakeLists.txt. These targets
# compile real custom game code, not stubs, using makepanda's source lists.
set(TT_SRC "${PROJECT_SOURCE_DIR}/panda/src")
set(TT_GENERATED "${PROJECT_BINARY_DIR}/toontown-generated")
file(MAKE_DIRECTORY "${TT_GENERATED}")

add_library(tt_otp STATIC
  "${TT_SRC}/nametag/nametag_composite1.cxx"
  "${TT_SRC}/nametag/nametag_composite2.cxx"
  "${TT_SRC}/movement/movement_composite1.cxx")
target_compile_definitions(tt_otp PRIVATE BUILDING_OTP)
target_include_directories(tt_otp PUBLIC
  "${TT_SRC}/otpbase" "${TT_SRC}/nametag" "${TT_SRC}/movement")
target_link_libraries(tt_otp PUBLIC panda p3direct)

find_package(BISON REQUIRED)
find_package(FLEX REQUIRED)
BISON_TARGET(TTParser "${TT_SRC}/dna/dnaParser.yxx" "${TT_GENERATED}/dnaParser.cxx"
  DEFINES_FILE "${TT_GENERATED}/dnaParser.h" COMPILE_FLAGS "-p dnayy")
FLEX_TARGET(TTLexer "${TT_SRC}/dna/dnaLexer.lxx" "${TT_GENERATED}/dnaLexer.cxx"
  COMPILE_FLAGS "-i -Pdnayy")
ADD_FLEX_BISON_DEPENDENCY(TTLexer TTParser)
add_library(tt_toontown STATIC
  "${TT_SRC}/dna/dnaLoader_composite1.cxx"
  "${TT_SRC}/dna/dnaLoader_composite2.cxx"
  "${TT_SRC}/suit/suit_composite1.cxx"
  "${TT_SRC}/pets/pets_composite1.cxx"
  ${BISON_TTParser_OUTPUTS} ${FLEX_TTLexer_OUTPUTS})
target_compile_definitions(tt_toontown PRIVATE BUILDING_TOONTOWN)
target_include_directories(tt_toontown PUBLIC
  "${TT_SRC}/toontownbase" "${TT_SRC}/dna" "${TT_SRC}/suit"
  "${TT_SRC}/pets" "${TT_GENERATED}")
target_link_libraries(tt_toontown PUBLIC tt_otp panda)

# These are already makepanda composite files. Keep the generated lexer and
# parser in separate translation units so their private yy symbols cannot mix.
set_target_properties(tt_otp tt_toontown PROPERTIES UNITY_BUILD OFF)

# The existing pandagles2 target requires EGL, which iOS does not provide.
# Supply our UIKit/EAGL pipe instead, without changing desktop display targets.
add_library(tt_uikit_input STATIC "${PROJECT_SOURCE_DIR}/TTPandaInputView.mm")
set_target_properties(tt_uikit_input PROPERTIES UNITY_BUILD OFF)
target_compile_options(tt_uikit_input PRIVATE -fobjc-arc -fno-fast-math -Wall -Werror)
# Upstream release-mode inline headers intentionally discard assertion-only
# locals. Treat those dependency headers as system headers, retaining -Werror
# for the new input adapter itself.
target_include_directories(tt_uikit_input SYSTEM PRIVATE
  "$<TARGET_PROPERTY:panda,INTERFACE_INCLUDE_DIRECTORIES>")
target_link_libraries(tt_uikit_input PRIVATE panda "-framework UIKit" "-framework CoreGraphics")

if(TARGET p3gles2gsg)
  add_library(tt_gles2 STATIC $<TARGET_OBJECTS:p3gles2gsg>)
  target_link_libraries(tt_gles2 PUBLIC panda p3glstuff PKG::GLES2)
  add_library(tt_uikit_display STATIC
    "${PROJECT_SOURCE_DIR}/TTGLESView.mm" "${PROJECT_SOURCE_DIR}/TTGraphicsPipe.mm")
  set_target_properties(tt_uikit_display PROPERTIES UNITY_BUILD OFF)
  target_compile_definitions(tt_uikit_display PRIVATE GLES_SILENCE_DEPRECATION)
  target_compile_options(tt_uikit_display PRIVATE -fobjc-arc -fno-fast-math -Wall -Werror)
  target_include_directories(tt_uikit_display SYSTEM PRIVATE
    "$<TARGET_PROPERTY:panda,INTERFACE_INCLUDE_DIRECTORIES>"
    "$<TARGET_PROPERTY:p3gles2gsg,INTERFACE_INCLUDE_DIRECTORIES>")
  target_link_libraries(tt_uikit_display PRIVATE tt_uikit_input tt_gles2
    "-framework UIKit" "-framework QuartzCore" "-framework CoreGraphics" "-framework OpenGLES")
  add_executable(tt_graphics_linkcheck EXCLUDE_FROM_ALL
    "${PROJECT_SOURCE_DIR}/TTGraphicsLinkCheck.mm")
  set_target_properties(tt_graphics_linkcheck PROPERTIES MACOSX_BUNDLE OFF)
  target_compile_options(tt_graphics_linkcheck PRIVATE -fobjc-arc)
  target_link_libraries(tt_graphics_linkcheck PRIVATE tt_uikit_display)
  if(NOT TARGET p3ode)
    message(FATAL_ERROR "The full-game device build requires the ODE physics target")
  endif()
  add_custom_target(tt_native_compile DEPENDS tt_graphics_linkcheck tt_otp tt_toontown pandaphysics p3ode p3openal_audio)
else()
  message(FATAL_ERROR "The device compilation gate requires the ES2 renderer target")
endif()

# Generate the actual game Python APIs with the host interrogate tool, then
# compile its wrappers against the device Python ABI. No module stubs.
if(INTERROGATE_PYTHON_INTERFACE)
  target_sources(tt_otp PRIVATE "${TT_SRC}/navigation/navigation_composite1.cxx")
  target_include_directories(tt_otp PUBLIC "${TT_SRC}/navigation"
    "${PROJECT_SOURCE_DIR}/dtool/src/interrogatedb")
  target_link_libraries(tt_otp PUBLIC PKG::PYTHON)
  file(GLOB TT_OTP_HEADERS CONFIGURE_DEPENDS
    "${TT_SRC}/nametag/*.h" "${TT_SRC}/movement/*.h" "${TT_SRC}/navigation/*.h")
  file(GLOB TT_TOONTOWN_HEADERS CONFIGURE_DEPENDS
    "${TT_SRC}/dna/*.h" "${TT_SRC}/suit/*.h" "${TT_SRC}/pets/*.h")
  # The generated parser header is private implementation, not a Python API.
  list(FILTER TT_TOONTOWN_HEADERS EXCLUDE REGEX "dnaParser\\.h$")
  target_interrogate(tt_otp ${TT_OTP_HEADERS})
  target_interrogate(tt_toontown ${TT_TOONTOWN_HEADERS})
  # Upstream add_python_module appends /<target>.in to a relative directory.
  # Root-level targets otherwise yield an empty directory and /tt_otp.in.
  set_target_properties(tt_otp tt_toontown PROPERTIES TARGET_BINDIR "${TT_GENERATED}")
  add_python_module(panda3d.otp tt_otp IMPORT panda3d.core IMPORT panda3d.direct)
  add_python_module(panda3d.toontown tt_toontown IMPORT panda3d.otp)
  add_executable(tt_python_linkcheck EXCLUDE_FROM_ALL
    "${PROJECT_SOURCE_DIR}/TTBuiltinModules.cxx" "${PROJECT_SOURCE_DIR}/TTLinkCheck.cxx")
  set_target_properties(tt_python_linkcheck PROPERTIES MACOSX_BUNDLE OFF)
  target_link_libraries(tt_python_linkcheck PRIVATE
    panda3d.core panda3d.direct panda3d.physics panda3d.ode panda3d.otp panda3d.toontown tt_uikit_display)
  # Real UIApplication entry point and controller, still without a distributable
  # runtime/content payload. This target proves native app-host compilation/link.
  add_executable(tt_ios_app MACOSX_BUNDLE EXCLUDE_FROM_ALL
    "${PROJECT_SOURCE_DIR}/TTApplication.mm"
    "${PROJECT_SOURCE_DIR}/TTGameViewController.mm"
    "${PROJECT_SOURCE_DIR}/TTEmbeddedRuntime.mm"
    "${PROJECT_SOURCE_DIR}/TTControlsView.mm"
    "${PROJECT_SOURCE_DIR}/TTGameInputBridge.mm"
    "${PROJECT_SOURCE_DIR}/TTBuiltinModules.cxx"
    "${PROJECT_SOURCE_DIR}/Device.prc")
  set_source_files_properties("${PROJECT_SOURCE_DIR}/Device.prc" PROPERTIES
    MACOSX_PACKAGE_LOCATION Resources)
  set_target_properties(tt_ios_app PROPERTIES UNITY_BUILD OFF OUTPUT_NAME OpenToontown
    MACOSX_BUNDLE_INFO_PLIST "${PROJECT_SOURCE_DIR}/Info.plist.in"
    BUILD_RPATH "@executable_path/Frameworks" XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED NO)
  target_compile_options(tt_ios_app PRIVATE "$<$<COMPILE_LANGUAGE:OBJCXX>:-fobjc-arc>"
    -fno-fast-math -Wall -Werror)
  target_link_libraries(tt_ios_app PRIVATE tt_uikit_display
    panda3d.core panda3d.direct panda3d.physics panda3d.ode panda3d.otp panda3d.toontown
    "-framework UIKit" "-framework QuartzCore" "-framework CoreGraphics")
  add_custom_target(tt_python_compile DEPENDS tt_python_linkcheck tt_ios_app)
endif()

# add_python_module participates in Panda's CMake export sets. Its custom
# native dependencies must be exported too, with relocatable include paths.
foreach(target tt_otp tt_toontown)
  get_target_property(TT_INCLUDES ${target} INTERFACE_INCLUDE_DIRECTORIES)
  set(TT_BUILD_INCLUDES)
  foreach(dir IN LISTS TT_INCLUDES)
    list(APPEND TT_BUILD_INCLUDES "$<BUILD_INTERFACE:${dir}>")
  endforeach()
  set_property(TARGET ${target} PROPERTY INTERFACE_INCLUDE_DIRECTORIES
    "${TT_BUILD_INCLUDES};$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/panda3d>")
endforeach()
install(TARGETS tt_otp tt_toontown EXPORT Core
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR} COMPONENT CoreDevel)
foreach(dir otpbase nametag movement navigation toontownbase dna suit pets)
  install(DIRECTORY "${TT_SRC}/${dir}/" DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/panda3d
    COMPONENT CoreDevel FILES_MATCHING PATTERN "*.h" PATTERN "*.I")
endforeach()
