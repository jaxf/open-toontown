#!/usr/bin/env bash
# Complete device payload for AltStore re-signing. No simulator or Apple login.
set -Eeuo pipefail
[[ $# == 2 && $1 == /* && $2 == /* ]] || {
  echo 'Usage: bash ios/assemble_ipa.sh /absolute/build-folder /absolute/new-output' >&2
  exit 2
}
TT_WORK=$1
TT_OUTPUT=$2
TT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
TT_RESOURCE_PIN=d00df01af876cc9c5d1a22329f394a9a50245e9c
if [[ ! -d "$TT_ROOT/resources" ]]; then
  git init "$TT_ROOT/resources"
  git -C "$TT_ROOT/resources" remote add origin https://github.com/open-toontown/resources.git
  git -C "$TT_ROOT/resources" fetch --depth=1 origin "$TT_RESOURCE_PIN"
  git -C "$TT_ROOT/resources" checkout --detach FETCH_HEAD
fi
[[ $(git -C "$TT_ROOT/resources" rev-parse HEAD) == "$TT_RESOURCE_PIN" ]] || {
  echo 'Resource revision does not match the hosted server.' >&2; exit 2;
}
python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
  --only-binary=:all: --require-hashes --target "$TT_WORK/runtime-packages" \
  -r "$TT_ROOT/ios/runtime-requirements.txt"
TT_HOST_PY="$TT_WORK/python-host/python.exe"
[[ -x "$TT_HOST_PY" ]] || TT_HOST_PY="$TT_WORK/python-host/python"
cd "$TT_ROOT"
"$TT_HOST_PY" -m ios.package_ipa --root "$TT_ROOT" --work "$TT_WORK" \
  --packages "$TT_WORK/runtime-packages" --output "$TT_OUTPUT"
