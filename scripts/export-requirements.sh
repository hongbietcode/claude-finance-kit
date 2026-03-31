#!/bin/bash
# Export requirements.txt from pyproject.toml

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYPROJECT_FILE="$SCRIPT_DIR/../pyproject.toml"

if [[ ! -f "$PYPROJECT_FILE" ]]; then
    echo "Error: pyproject.toml not found at $PYPROJECT_FILE"
    exit 1
fi

echo "# Core dependencies"

# Extract core dependencies
awk '
/^dependencies = \[$/,/^\]$/ {
    if ($0 ~ /^[[:space:]]*".*"[[:space:]]*,?[[:space:]]*$/) {
        gsub(/^[[:space:]]*"/, "")
        gsub(/"[[:space:]]*,?[[:space:]]*$/, "")
        print $0
    }
}' "$PYPROJECT_FILE"

echo ""
echo "# Optional dependencies"

# Extract optional dependencies
awk '
BEGIN { in_optional = 0; current_extra = "" }

/^\[project\.optional-dependencies\]$/ {
    in_optional = 1
    next
}

/^\[/ && !/^\[project\.optional-dependencies\]$/ {
    in_optional = 0
}

in_optional && /^[a-zA-Z_][a-zA-Z0-9_-]* = \[/ {
    # Extract extra name
    gsub(/ = \[.*$/, "")
    current_extra = $0
    is_empty = ($0 ~ /= \[\]$/)

    if (!is_empty) {
        print ""
        print "# Extra: " current_extra
    }
    next
}

in_optional && current_extra != "" && /^[[:space:]]*".*"[[:space:]]*,?[[:space:]]*$/ {
    gsub(/^[[:space:]]*"/, "")
    gsub(/"[[:space:]]*,?[[:space:]]*$/, "")
    if ($0 != "") print $0
}

in_optional && /^\]$/ {
    current_extra = ""
}
' "$PYPROJECT_FILE"