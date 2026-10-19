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
# Compile the existing ES2 state guardian now; a UIKit/EAGL pipe must still
# supply the drawable and context before it can render the actual game.
if(TARGET p3gles2gsg)
  add_library(tt_gles2 STATIC $<TARGET_OBJECTS:p3gles2gsg>)
  target_link_libraries(tt_gles2 PUBLIC panda)
  add_custom_target(tt_native_compile DEPENDS tt_otp tt_toontown tt_gles2 pandaphysics p3openal_audio)
else()
  message(FATAL_ERROR "The device compilation gate requires the ES2 renderer target")
endif()

# Generate the actual game Python APIs with the host interrogate tool, then
# compile its wrappers against the device Python ABI. No module stubs.
if(INTERROGATE_PYTHON_INTERFACE)
  target_sources(tt_otp PRIVATE "${TT_SRC}/navigation/navigation_composite1.cxx")
  target_include_directories(tt_otp PUBLIC "${TT_SRC}/navigation")
  target_link_libraries(tt_otp PUBLIC PKG::PYTHON)
  file(GLOB TT_OTP_HEADERS CONFIGURE_DEPENDS
    "${TT_SRC}/nametag/*.h" "${TT_SRC}/movement/*.h" "${TT_SRC}/navigation/*.h")
  file(GLOB TT_TOONTOWN_HEADERS CONFIGURE_DEPENDS
    "${TT_SRC}/dna/*.h" "${TT_SRC}/suit/*.h" "${TT_SRC}/pets/*.h")
  # The generated parser header is private implementation, not a Python API.
  list(FILTER TT_TOONTOWN_HEADERS EXCLUDE REGEX "dnaParser\\.h$")
  target_interrogate(tt_otp ${TT_OTP_HEADERS})
  target_interrogate(tt_toontown ${TT_TOONTOWN_HEADERS})
  add_python_module(panda3d.otp tt_otp IMPORT panda3d.core IMPORT panda3d.direct)
  add_python_module(panda3d.toontown tt_toontown IMPORT panda3d.otp)
  add_custom_target(tt_python_compile DEPENDS
    panda3d.core panda3d.direct panda3d.physics panda3d.otp panda3d.toontown)
endif()
