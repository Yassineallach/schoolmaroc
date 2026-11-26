#!/usr/bin/env bash
# Writes local.properties for a CI build from environment variables (GitHub secrets).
# Every value is optional: without the keystore the release is unsigned, without the
# AdMob IDs it shows Google's test ads.
set -euo pipefail

# .properties escaping: a backslash must be doubled; keep everything else literal.
esc() { printf '%s' "$1" | sed 's/\\/\\\\/g'; }

out="${1:-local.properties}"
: > "$out"
if [ -n "${ANDROID_HOME:-}" ]; then echo "sdk.dir=$(esc "$ANDROID_HOME")" >> "$out"; fi

if [ -n "${KEYSTORE_BASE64:-}" ]; then
  ks="${RUNNER_TEMP:-/tmp}/upload-keystore.jks"
  printf '%s' "$KEYSTORE_BASE64" | tr -d '\r\n ' | base64 -d > "$ks"
  {
    echo "release.storeFile=$(esc "$ks")"
    echo "release.storePassword=$(esc "${KEYSTORE_PASSWORD:?KEYSTORE_PASSWORD secret is missing}")"
    echo "release.keyAlias=$(esc "${KEY_ALIAS:-upload}")"
    echo "release.keyPassword=$(esc "${KEY_PASSWORD:-${KEYSTORE_PASSWORD}}")"
  } >> "$out"
  echo "Signing: upload key found"
else
  echo "::warning::No KEYSTORE_BASE64 secret: the release will be UNSIGNED (Play will not accept it)."
fi

if [ -n "${ADMOB_APP_ID:-}" ] && [ -n "${ADMOB_NATIVE_UNIT_ID:-}" ]; then
  echo "admob.appId=$(esc "$ADMOB_APP_ID")" >> "$out"
  echo "admob.nativeUnitId=$(esc "$ADMOB_NATIVE_UNIT_ID")" >> "$out"
fi
echo "admob.testAds=${TEST_ADS:-false}" >> "$out"
if [ "${TEST_ADS:-false}" = "true" ] || [ -z "${ADMOB_APP_ID:-}" ]; then
  echo "::warning::This release shows Google's TEST ads."
else
  echo "AdMob: this release shows your REAL ads."
fi
