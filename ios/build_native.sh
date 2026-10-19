#!/usr/bin/env bash
# Reproducible first native device compilation; never presents it as an IPA.
set -Eeuo pipefail
[[ $# == 2 && $1 =~ ^(python|panda)$ ]] || { echo 'Usage: bash ios/build_native.sh python|panda /absolute/build-folder' >&2; exit 2; }
[[ $(uname -s) == Darwin ]] || { echo 'A Mac with full Xcode is required (the cloud workflow supplies it).' >&2; exit 2; }
TT_COMPONENT=$1
TT_WORK=$2
[[ $TT_WORK == /* && $TT_WORK != / ]] || { echo 'Use an absolute build folder, not /.' >&2; exit 2; }
TT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
TT_SDK=$(xcrun --sdk iphoneos --show-sdk-path)
[[ -d $TT_SDK ]] || exit 2
TT_JOBS=$(sysctl -n hw.logicalcpu)
TT_ENGINE=06615744481946654610833679a0893589114504
TT_CPYTHON=8183fa5e3f78ca6ab862de7fb8b14f3d929421e0
mkdir -p "$TT_WORK"
fetch_source() {
  local url=$1 revision=$2 folder=$3
  if [[ ! -d $folder ]]; then
    git init "$folder"
    git -C "$folder" remote add origin "$url"
    git -C "$folder" fetch --depth=1 origin "$revision"
    git -C "$folder" checkout --detach FETCH_HEAD
  fi
  [[ $(git -C "$folder" rev-parse HEAD) == "$revision" ]] || { echo 'Source revision mismatch.' >&2; exit 2; }
}
xcodebuild -version
printf 'Device SDK: %s\nComponent: %s\n' "$TT_SDK" "$TT_COMPONENT"
if [[ $TT_COMPONENT == python ]]; then
  TT_SOURCE="$TT_WORK/cpython"
  fetch_source https://github.com/python/cpython.git "$TT_CPYTHON" "$TT_SOURCE"
  mkdir -p "$TT_WORK/python-host" "$TT_WORK/python-device" "$TT_WORK/python-install"
  # Same source revision for the build interpreter and target framework.
  cd "$TT_WORK/python-host"
  "$TT_SOURCE/configure" --without-ensurepip --disable-test-modules
  make -j "$TT_JOBS"
  TT_HOST_PY="$TT_WORK/python-host/python.exe"
  [[ -x $TT_HOST_PY ]] || TT_HOST_PY="$TT_WORK/python-host/python"
  [[ -x $TT_HOST_PY ]] || exit 2
  case $(uname -m) in
    arm64) TT_BUILD=arm64-apple-darwin ;;
    x86_64) TT_BUILD=x86_64-apple-darwin ;;
    *) exit 2 ;;
  esac
  # Avoid accidentally linking macOS Homebrew dependencies into iOS.
  export PATH="$TT_SOURCE/iOS/Resources/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/Apple/usr/bin"
  unset CPATH LIBRARY_PATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH PKG_CONFIG_PATH
  cd "$TT_WORK/python-device"
  "$TT_SOURCE/configure" --host=arm64-apple-ios15.0 --build="$TT_BUILD" \
    --enable-framework="$TT_WORK/python-install" --with-build-python="$TT_HOST_PY" \
    --without-ensurepip --disable-test-modules
  make -j "$TT_JOBS"
  make install
  TT_BINARY="$TT_WORK/python-install/Python.framework/Python"
  xcrun lipo "$TT_BINARY" -verify_arch arm64
  xcrun vtool -show-build "$TT_BINARY" | tee "$TT_WORK/python-platform.txt"
  grep -Eq 'platform[[:space:]]+IOS$' "$TT_WORK/python-platform.txt"
  printf '%s\n' 'PYTHON DEVICE FRAMEWORK COMPILED. Third-party modules and game integration still required.'
else
  TT_SOURCE="$TT_WORK/panda"
  fetch_source https://github.com/open-toontown/panda3d.git "$TT_ENGINE" "$TT_SOURCE"
  python3 "$TT_ROOT/ios/prepare_engine.py" "$TT_SOURCE"
  TT_CMAKE=$(command -v cmake)
  [[ -n $TT_CMAKE ]] || { echo 'cmake is required.' >&2; exit 2; }
  TT_OPTIONS=()
  # No desktop dependencies may satisfy an iPhone build. Add target-built
  # dependencies and Python bindings in the next runtime integration stage.
  for package in PYTHON OPENSSL ZLIB JPEG PNG TIFF OPENEXR SQUISH ASSIMP FCOLLADA EIGEN FFTW FFMPEG SWSCALE SWRESAMPLE VORBIS OPUS FMODEX OPENAL FREETYPE HARFBUZZ GTK3 BULLET ODE SPEEDTREE GL GLES1 DX9 CG CGGL CGD3D9 X11 EGL OPENCV ARTOOLKIT VRPN MIMALLOC; do
    TT_OPTIONS+=("-DHAVE_${package}=OFF")
  done
  "$TT_CMAKE" -S "$TT_SOURCE" -B "$TT_WORK/panda-device" -G 'Unix Makefiles' \
    -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT="$TT_SDK" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0 \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
    -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
    -DCMAKE_IGNORE_PREFIX_PATH='/opt/homebrew;/usr/local' \
    -DCMAKE_C_FLAGS=-DBUILD_IPHONE -DCMAKE_CXX_FLAGS=-DBUILD_IPHONE \
    -DCMAKE_OBJCXX_FLAGS=-DBUILD_IPHONE \
    -DBUILD_SHARED_LIBS=OFF -DBUILD_IPHONE=iPhoneOS \
    -DBUILD_PANDATOOL=OFF -DBUILD_CONTRIB=OFF -DBUILD_MODELS=OFF \
    -DBUILD_TESTS=OFF -DBUILD_TOOLS=OFF -DBUILD_INTERROGATE=OFF \
    -DINTERROGATE_PYTHON_INTERFACE=OFF -DINTERROGATE_C_INTERFACE=OFF \
    -DHAVE_AUDIO=OFF -DHAVE_COCOA=OFF -DHAVE_GLES2=ON \
    -DOPENGLES2_FOUND=ON -DOPENGLES2_INCLUDE_DIR="$TT_SDK/System/Library/Frameworks/OpenGLES.framework/Headers" \
    -DOPENGLES2_LIBRARY="$TT_SDK/System/Library/Frameworks/OpenGLES.framework" \
    "${TT_OPTIONS[@]}"
  "$TT_CMAKE" --build "$TT_WORK/panda-device" --parallel "$TT_JOBS" \
    --target tt_native_compile
  printf '%s\n' 'PANDA DEVICE C++ COMPILED. No Python bindings, UIKit window or playable IPA yet.'
fi
