#!/usr/bin/env bash
set -euo pipefail
# Remove prototype/backup debris
patterns=(
  "ui-mobile/test_venmo_nav.html"
  "ui-mobile/**/*.bak" "ui-mobile/**/*.orig" "ui-mobile/**/*backup*" "ui-mobile/**/*old*" "ui-mobile/**/*.tmp"
  "nerava-backend-v9/app/*_demo.py"
)
for p in "${patterns[@]}"; do
  git rm -rf --cached --ignore-unmatch $p 2>/dev/null || true
  rm -rf $p 2>/dev/null || true
done
echo "Cleanup complete."