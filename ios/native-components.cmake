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
  COMPILE_FLAGS "-i")
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

# The existing pandagles2 target requires EGL, which iOS does not provide.
# Compile the existing ES2 state guardian now; a UIKit/EAGL pipe must still
# supply the drawable and context before it can render the actual game.
if(TARGET p3gles2gsg)
  add_library(tt_gles2 STATIC $<TARGET_OBJECTS:p3gles2gsg>)
  target_link_libraries(tt_gles2 PUBLIC panda)
  add_custom_target(tt_native_compile DEPENDS tt_otp tt_toontown tt_gles2 pandaphysics)
else()
  message(FATAL_ERROR "The device compilation gate requires the ES2 renderer target")
endif()
