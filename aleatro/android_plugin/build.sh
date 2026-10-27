#!/bin/sh
# Builds the plugin AAR and copies it into res://addons/aleatro_pgs/bin.
# Needs the Android build template (Project > Install Android Build Template)
# for Godot's classes.
set -e
cd "$(dirname "$0")"
mkdir -p libs
unzip -o -q -j ../android/build/libs/release/godot-lib.template_release.aar classes.jar -d libs
mv libs/classes.jar libs/godot-classes.jar
../android/build/gradlew -p . assembleRelease
mkdir -p ../addons/aleatro_pgs/bin
cp build/outputs/aar/aleatro_pgs-release.aar ../addons/aleatro_pgs/bin/aleatro_pgs.aar
echo "built ../addons/aleatro_pgs/bin/aleatro_pgs.aar"
