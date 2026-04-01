#!/bin/bash
# Package claude-finance-kit plugin files into a zip for Claude Code installation
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="claude-finance-kit"
VERSION=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
OUTPUT="$PROJECT_DIR/dist/${SKILL_NAME}-plugin-v${VERSION}.zip"

mkdir -p "$PROJECT_DIR/dist"
rm -f "$OUTPUT"

cd "$PROJECT_DIR"

echo "Packaging $SKILL_NAME plugin v${VERSION}..."

zip -r9 "$OUTPUT" \
    ".claude-plugin/" \
    "skills/" \
    "commands/" \
    "agents/" \
    "references/" \
    "hooks/" \
    "docs/" \
    "CLAUDE.md" \
    -x "*.DS_Store"

FILE_COUNT=$(unzip -l "$OUTPUT" | tail -1 | awk '{print $2}')
FILE_SIZE=$(du -h "$OUTPUT" | cut -f1)

echo ""
echo "Done: $OUTPUT"
echo "Files: $FILE_COUNT | Size: $FILE_SIZE"
echo ""
echo "Install: unzip into ~/.claude/plugins/cache/$SKILL_NAME/"
echo "Or test: claude --plugin-dir ."
