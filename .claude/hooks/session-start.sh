#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Verify JSON content files are valid
find "${CLAUDE_PROJECT_DIR:-$(pwd)}/content" -name "*.json" | while read -r f; do
  python3 -m json.tool "$f" > /dev/null
done

echo "Session start: environment ready."
