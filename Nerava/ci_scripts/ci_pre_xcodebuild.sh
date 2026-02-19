#!/bin/bash
# Xcode Cloud Pre-Xcodebuild Script
# This script runs before xcodebuild is invoked

set -e

echo "=== Nerava iOS CI Pre-Xcodebuild Script ==="
echo "Xcode version: $(xcodebuild -version)"
echo "Available SDKs: $(xcodebuild -showsdks | grep -i ios)"
echo "Build Number: $CI_BUILD_NUMBER"
echo "Workflow: $CI_WORKFLOW"
echo ""

# Verify minimum Xcode version for Swift 6 features
XCODE_VERSION=$(xcodebuild -version | grep "Xcode" | cut -d' ' -f2)
echo "Detected Xcode version: $XCODE_VERSION"

# Swift 6 features require Xcode 16+
MAJOR_VERSION=$(echo "$XCODE_VERSION" | cut -d'.' -f1)
if [ "$MAJOR_VERSION" -lt 16 ]; then
    echo "WARNING: Swift 6 features require Xcode 16+. Current version: $XCODE_VERSION"
    echo "Consider selecting Xcode 16+ in Xcode Cloud workflow settings."
fi

echo "=== Pre-Xcodebuild Complete ==="
