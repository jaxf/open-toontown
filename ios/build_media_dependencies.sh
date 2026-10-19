#!/usr/bin/env bash
# Device-only image/font libraries. No host tools or simulator binaries.
set -Eeuo pipefail
[[ $# == 1 && $1 == /* && $1 != / && $(uname -s) == Darwin ]] || {
  echo 'Usage on macOS: bash ios/build_media_dependencies.sh /absolute/build-folder' >&2
  exit 2
}
TT_MEDIA_WORK=$1
TT_MEDIA_SDK=$(xcrun --sdk iphoneos --show-sdk-path)
TT_MEDIA_JOBS=$(sysctl -n hw.logicalcpu)
TT_MEDIA_PREFIX="$TT_MEDIA_WORK/dependencies"
mkdir -p "$TT_MEDIA_WORK/media-sources" "$TT_MEDIA_PREFIX/share/licenses"
unset CPATH LIBRARY_PATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH PKG_CONFIG_PATH
export PKG_CONFIG_LIBDIR="$TT_MEDIA_PREFIX/lib/pkgconfig"

fetch() {
  local name=$1 repo=$2 revision=$3
  local source="$TT_MEDIA_WORK/media-sources/$name"
  if [[ ! -d $source ]]; then
    git init "$source"
    git -C "$source" remote add origin "https://github.com/$repo.git"
    git -C "$source" fetch --depth=1 origin "$revision"
    git -C "$source" checkout --detach FETCH_HEAD
  fi
  [[ $(git -C "$source" rev-parse HEAD) == "$revision" ]] || {
    echo "Source revision mismatch: $name" >&2; exit 2;
  }
}

build() {
  local name=$1
  shift
  cmake -S "$TT_MEDIA_WORK/media-sources/$name" -B "$TT_MEDIA_WORK/$name-device" \
    -G 'Unix Makefiles' -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_SYSROOT="$TT_MEDIA_SDK" -DCMAKE_OSX_ARCHITECTURES=arm64 \
    -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$TT_MEDIA_PREFIX" -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
    -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
    -DCMAKE_IGNORE_PREFIX_PATH='/opt/homebrew;/usr/local' "$@"
  cmake --build "$TT_MEDIA_WORK/$name-device" --parallel "$TT_MEDIA_JOBS"
  cmake --install "$TT_MEDIA_WORK/$name-device"
}

# Link the iPhone SDK's zlib, never the build Mac's copy.
TT_ZLIB=(-DZLIB_INCLUDE_DIR="$TT_MEDIA_SDK/usr/include"
         -DZLIB_LIBRARY="$TT_MEDIA_SDK/usr/lib/libz.tbd")
[[ -f "$TT_MEDIA_SDK/usr/lib/libz.tbd" ]] || exit 2

# libpng 1.6.59, libjpeg-turbo 3.2.0, FreeType 2.15.0.
fetch png pnggroup/libpng cd952f49f95bb27154ae77dbb103032d95f6e580
build png -DPNG_SHARED=OFF -DPNG_STATIC=ON -DPNG_FRAMEWORK=OFF \
  -DPNG_TESTS=OFF -DPNG_TOOLS=OFF "${TT_ZLIB[@]}"
fetch jpeg libjpeg-turbo/libjpeg-turbo c85e6b905bf237038faa936dab160ebfc5da0344
build jpeg -DENABLE_SHARED=OFF -DENABLE_STATIC=ON -DWITH_TURBOJPEG=OFF \
  -DWITH_TOOLS=OFF -DWITH_TESTS=OFF
fetch freetype freetype/freetype 37515cf56ba3349656049edbed89ffc6f6466f2d
build freetype -DFT_REQUIRE_ZLIB=ON -DFT_REQUIRE_PNG=ON \
  -DFT_DISABLE_BZIP2=ON -DFT_DISABLE_HARFBUZZ=ON -DFT_DISABLE_BROTLI=ON \
  -DFT_DISABLE_HVF=ON -DPNG_PNG_INCLUDE_DIR="$TT_MEDIA_PREFIX/include" \
  -DPNG_LIBRARY_RELEASE="$TT_MEDIA_PREFIX/lib/libpng16.a" "${TT_ZLIB[@]}"

# Ogg 1.3.6 and Vorbis 1.3.7 decode the game's music and effects.
fetch ogg xiph/ogg be05b13e98b048f0b5a0f5fa8ce514d56db5f822
build ogg -DBUILD_TESTING=OFF -DBUILD_FRAMEWORK=OFF -DINSTALL_DOCS=OFF
fetch vorbis xiph/vorbis 0657aee69dec8508a0011f47f3b69d7538e9d262
build vorbis -DBUILD_TESTING=OFF -DBUILD_FRAMEWORK=OFF \
  -DOGG_INCLUDE_DIR="$TT_MEDIA_PREFIX/include" \
  -DOGG_LIBRARY="$TT_MEDIA_PREFIX/lib/libogg.a"

for archive in libpng16.a libjpeg.a libfreetype.a libogg.a libvorbis.a libvorbisfile.a; do
  xcrun lipo "$TT_MEDIA_PREFIX/lib/$archive" -verify_arch arm64
done
# Retain upstream notices for the eventual app payload's acknowledgements.
for name in png jpeg freetype ogg vorbis; do
  mkdir -p "$TT_MEDIA_PREFIX/share/licenses/$name"
done
cp "$TT_MEDIA_WORK/media-sources/png/LICENSE" "$TT_MEDIA_PREFIX/share/licenses/png/"
cp "$TT_MEDIA_WORK/media-sources/jpeg/LICENSE.md" "$TT_MEDIA_WORK/media-sources/jpeg/README.ijg" \
  "$TT_MEDIA_PREFIX/share/licenses/jpeg/"
cp "$TT_MEDIA_WORK/media-sources/freetype/LICENSE.TXT" \
  "$TT_MEDIA_WORK/media-sources/freetype/docs/FTL.TXT" \
  "$TT_MEDIA_WORK/media-sources/freetype/docs/GPLv2.TXT" \
  "$TT_MEDIA_PREFIX/share/licenses/freetype/"
for name in ogg vorbis; do
  cp "$TT_MEDIA_WORK/media-sources/$name/COPYING" "$TT_MEDIA_PREFIX/share/licenses/$name/"
done
echo 'DEVICE MEDIA LIBRARIES BUILT. Decoding, rendering and playback still require device testing.'
