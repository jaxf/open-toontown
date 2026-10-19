#!/usr/bin/env bash
# OpenSSL for Panda HTTPClient and CPython's SSL/hash modules, iPhone only.
set -Eeuo pipefail
[[ $# == 1 && $1 == /* && $1 != / && $(uname -s) == Darwin ]] || {
  echo 'Usage on macOS: bash ios/build_crypto_dependency.sh /absolute/build-folder' >&2
  exit 2
}
TT_CRYPTO_WORK=$1
TT_CRYPTO_SOURCE="$TT_CRYPTO_WORK/openssl"
TT_CRYPTO_PREFIX="$TT_CRYPTO_WORK/dependencies"
TT_CRYPTO_PIN=45e844fa2a14ec92d146bd8f5778ac130b6625fb # OpenSSL 3.5.9
if [[ ! -d $TT_CRYPTO_SOURCE ]]; then
  git init "$TT_CRYPTO_SOURCE"
  git -C "$TT_CRYPTO_SOURCE" remote add origin https://github.com/openssl/openssl.git
  git -C "$TT_CRYPTO_SOURCE" fetch --depth=1 origin "$TT_CRYPTO_PIN"
  git -C "$TT_CRYPTO_SOURCE" checkout --detach FETCH_HEAD
fi
[[ $(git -C "$TT_CRYPTO_SOURCE" rev-parse HEAD) == "$TT_CRYPTO_PIN" ]] || {
  echo 'OpenSSL source revision mismatch.' >&2; exit 2;
}
unset CPATH LIBRARY_PATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH PKG_CONFIG_PATH CC CXX
export SDKROOT=$(xcrun --sdk iphoneos --show-sdk-path)
mkdir -p "$TT_CRYPTO_WORK/openssl-device"
cd "$TT_CRYPTO_WORK/openssl-device"
perl "$TT_CRYPTO_SOURCE/Configure" ios64-xcrun -miphoneos-version-min=15.0 \
  no-shared no-tests no-module no-apps no-docs \
  --prefix="$TT_CRYPTO_PREFIX" --libdir=lib --openssldir="$TT_CRYPTO_PREFIX/ssl"
make -j "$(sysctl -n hw.logicalcpu)" build_libs
make install_sw
for archive in libssl.a libcrypto.a; do
  xcrun lipo "$TT_CRYPTO_PREFIX/lib/$archive" -verify_arch arm64
done
mkdir -p "$TT_CRYPTO_PREFIX/share/licenses/openssl"
cp "$TT_CRYPTO_SOURCE/LICENSE.txt" "$TT_CRYPTO_PREFIX/share/licenses/openssl/"
echo 'DEVICE OPENSSL BUILT. Certificate trust packaging and device HTTPS tests remain required.'
