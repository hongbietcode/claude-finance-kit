#!/bin/bash
# Download and install claude-finance-kit plugin into ~/.claude/
# Usage: bash scripts/install-claude-plugin.sh [version]
# Example: bash scripts/install-claude-plugin.sh v0.1.8
set -e

REPO="hongbietcode/claude-finance-kit"
PLUGIN_NAME="claude-finance-kit"
CLAUDE_DIR="$HOME/.claude"
INSTALL_DIR="$CLAUDE_DIR/plugins/cache/$PLUGIN_NAME"

if [ -n "$1" ]; then
    TAG="$1"
else
    TAG=$(gh release view --repo "$REPO" --json tagName --jq '.tagName' 2>/dev/null)
    if [ -z "$TAG" ]; then
        echo "Error: could not fetch latest release. Pass version manually: $0 v0.1.8"
        exit 1
    fi
fi

VERSION="${TAG#v}"
ZIP_NAME="${PLUGIN_NAME}-plugin-${TAG}.zip"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "Installing $PLUGIN_NAME plugin $TAG..."

gh release download "$TAG" \
    --repo "$REPO" \
    --pattern "$ZIP_NAME" \
    --dir "$TMP_DIR" \
    --clobber

if [ ! -f "$TMP_DIR/$ZIP_NAME" ]; then
    echo "Error: failed to download $ZIP_NAME"
    exit 1
fi

mkdir -p "$INSTALL_DIR/$VERSION"
unzip -qo "$TMP_DIR/$ZIP_NAME" -d "$INSTALL_DIR/$VERSION"

echo ""
echo "Installed: $INSTALL_DIR/$VERSION"
echo ""
echo "Contents:"
ls -1 "$INSTALL_DIR/$VERSION"
echo ""
echo "Done. Plugin files available at $INSTALL_DIR/$VERSION/"
