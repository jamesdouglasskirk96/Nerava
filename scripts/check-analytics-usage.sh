#!/bin/bash
# Check for direct PostHog usage outside analytics wrappers
# This script should be run in CI to ensure analytics best practices

set -e

ERRORS=0

echo "Checking for direct PostHog usage..."

# Check frontend apps for direct posthog imports/calls
for app in apps/driver apps/merchant apps/admin apps/landing; do
  if [ -d "$app" ]; then
    echo "Checking $app..."
    
    # Find files that import posthog directly (should only be in analytics wrappers)
    DIRECT_IMPORTS=$(find "$app/src" "$app/app" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
      -not -path "*/analytics/*" \
      -not -path "*/node_modules/*" \
      -exec grep -l "from ['\"]posthog-js['\"]" {} \; 2>/dev/null || true)
    
    if [ -n "$DIRECT_IMPORTS" ]; then
      echo "ERROR: Direct posthog-js imports found outside analytics wrappers:"
      echo "$DIRECT_IMPORTS"
      ERRORS=$((ERRORS + 1))
    fi
    
    # Find files that call posthog.capture directly (should use wrapper)
    DIRECT_CAPTURE=$(find "$app/src" "$app/app" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
      -not -path "*/analytics/*" \
      -not -path "*/node_modules/*" \
      -exec grep -l "posthog\.capture(" {} \; 2>/dev/null || true)
    
    if [ -n "$DIRECT_CAPTURE" ]; then
      echo "ERROR: Direct posthog.capture() calls found outside analytics wrappers:"
      echo "$DIRECT_CAPTURE"
      ERRORS=$((ERRORS + 1))
    fi
  fi
done

# Check backend for direct posthog usage (should use analytics service)
if [ -d "backend/app" ]; then
  echo "Checking backend..."
  
  DIRECT_POSTHOG=$(find backend/app -type f -name "*.py" \
    -not -path "*/services/analytics.py" \
    -not -path "*/node_modules/*" \
    -exec grep -l "import posthog\|from posthog\|posthog\." {} \; 2>/dev/null || true)
  
  if [ -n "$DIRECT_POSTHOG" ]; then
    echo "ERROR: Direct posthog usage found outside analytics service:"
    echo "$DIRECT_POSTHOG"
    ERRORS=$((ERRORS + 1))
  fi
fi

if [ $ERRORS -eq 0 ]; then
  echo "✓ No direct PostHog usage found. All analytics go through wrappers."
  exit 0
else
  echo "✗ Found $ERRORS error(s). Please use analytics wrappers instead of direct PostHog calls."
  exit 1
fi




