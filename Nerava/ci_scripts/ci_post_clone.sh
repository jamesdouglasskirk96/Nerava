#!/bin/bash
# Xcode Cloud Post-Clone Script
# This script runs after the repository is cloned

set -e

echo "=== Nerava iOS CI Post-Clone Script ==="
echo "Xcode version: $(xcodebuild -version | head -1)"
echo "Swift version: $(swift --version | head -1)"

# Navigate to project directory
cd "$CI_PRIMARY_REPOSITORY_PATH/Nerava"

# Print environment info for debugging
echo "CI_PRIMARY_REPOSITORY_PATH: $CI_PRIMARY_REPOSITORY_PATH"
echo "CI_XCODE_PROJECT: $CI_XCODE_PROJECT"
echo "CI_XCODE_SCHEME: $CI_XCODE_SCHEME"

# Resolve any Swift package dependencies
echo "Resolving Swift package dependencies..."
xcodebuild -resolvePackageDependencies -project Nerava.xcodeproj -scheme Nerava || true

echo "=== CI Post-Clone Complete ==="
