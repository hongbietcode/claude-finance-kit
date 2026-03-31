#!/bin/bash
# Download and install claude-finance-kit plugin into ~/.claude/
# Usage: GITHUB_TOKEN=ghp_xxx bash scripts/install-claude-plugin.sh [version]
# Example: bash scripts/install-claude-plugin.sh v0.1.8
set -e

REPO="hongbietcode/claude-finance-kit"
MARKETPLACE="hongbietcode-claude-finance-kit"
PLUGIN_NAME="claude-finance-kit"
CLAUDE_DIR="$HOME/.claude"
MARKETPLACE_DIR="$CLAUDE_DIR/plugins/marketplaces/$MARKETPLACE"
CACHE_DIR="$CLAUDE_DIR/plugins/cache/$MARKETPLACE/$PLUGIN_NAME"
REGISTRY="$CLAUDE_DIR/plugins/installed_plugins.json"
MARKETPLACES="$CLAUDE_DIR/plugins/known_marketplaces.json"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN env var required"
    echo "Usage: GITHUB_TOKEN=ghp_xxx bash $0 [version]"
    exit 1
fi

if [ -n "$1" ]; then
    TAG="$1"
else
    TAG=$(curl -fsSL \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO/releases/latest" \
        | grep '"tag_name"' | sed 's/.*: "\(.*\)".*/\1/')
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

ASSET_URL=$(curl -fsSL \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/releases/tags/$TAG" \
    | grep -B3 "\"name\": \"$ZIP_NAME\"" | grep '"url"' | sed 's/.*"\(https[^"]*\)".*/\1/')

if [ -z "$ASSET_URL" ]; then
    echo "Error: could not find $ZIP_NAME in release $TAG"
    exit 1
fi

curl -fsSL \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/octet-stream" \
    -o "$TMP_DIR/$ZIP_NAME" \
    "$ASSET_URL"

if [ ! -f "$TMP_DIR/$ZIP_NAME" ]; then
    echo "Error: failed to download $ZIP_NAME"
    exit 1
fi

GIT_SHA=$(curl -fsSL \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/git/ref/tags/$TAG" \
    | grep '"sha"' | head -1 | sed 's/.*"\([a-f0-9]\{40\}\)".*/\1/')

rm -rf "$CACHE_DIR"
mkdir -p "$CACHE_DIR/$VERSION"
unzip -qo "$TMP_DIR/$ZIP_NAME" -d "$CACHE_DIR/$VERSION"

rm -rf "$MARKETPLACE_DIR"
mkdir -p "$MARKETPLACE_DIR/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME"

cat > "$MARKETPLACE_DIR/.claude-plugin/marketplace.json" <<MKJSON
{
  "name": "$MARKETPLACE",
  "description": "Vietnamese stock analysis and market research plugin for Claude Code",
  "owner": {
    "name": "claude-finance-kit contributors"
  },
  "plugins": [
    {
      "name": "$PLUGIN_NAME",
      "description": "Vietnamese stock analysis — fundamentals, technicals, macro, news, screening, fund analysis",
      "category": "productivity",
      "source": "./plugins/$PLUGIN_NAME",
      "homepage": "https://github.com/$REPO"
    }
  ]
}
MKJSON

cp -r "$CACHE_DIR/$VERSION/.claude-plugin" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/"
cp -r "$CACHE_DIR/$VERSION/skills" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/" 2>/dev/null || true
cp -r "$CACHE_DIR/$VERSION/agents" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/" 2>/dev/null || true
cp -r "$CACHE_DIR/$VERSION/references" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/" 2>/dev/null || true
cp -r "$CACHE_DIR/$VERSION/docs" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/" 2>/dev/null || true

NOW=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
PLUGIN_KEY="${PLUGIN_NAME}@${MARKETPLACE}"
INSTALL_PATH="$CACHE_DIR/$VERSION"

python3 -c "
import json

registry_path = '$REGISTRY'
marketplaces_path = '$MARKETPLACES'

try:
    reg = json.load(open(registry_path))
except (FileNotFoundError, json.JSONDecodeError):
    reg = {'version': 2, 'plugins': {}}

reg['plugins']['$PLUGIN_KEY'] = [{
    'scope': 'user',
    'installPath': '$INSTALL_PATH',
    'version': '$VERSION',
    'installedAt': '$NOW',
    'lastUpdated': '$NOW',
    'gitCommitSha': '${GIT_SHA:-unknown}'
}]
json.dump(reg, open(registry_path, 'w'), indent=2)

try:
    mkts = json.load(open(marketplaces_path))
except (FileNotFoundError, json.JSONDecodeError):
    mkts = {}

mkts['$MARKETPLACE'] = {
    'source': {
        'source': 'github',
        'repo': '$REPO'
    },
    'installLocation': '$MARKETPLACE_DIR',
    'lastUpdated': '$NOW'
}
json.dump(mkts, open(marketplaces_path, 'w'), indent=2)
"

TOKEN_B64=$(echo -n "$GITHUB_TOKEN" | base64)
echo "Replacing token placeholder in installed files..."
REPLACED=0
while IFS= read -r -d '' file; do
    if grep -q '<YOUR_BASE64_ENCODED_GITHUB_TOKEN>' "$file" 2>/dev/null; then
        sed -i '' "s|<YOUR_BASE64_ENCODED_GITHUB_TOKEN>|$TOKEN_B64|g" "$file"
        REPLACED=$((REPLACED + 1))
        echo "  Updated: ${file#$CLAUDE_DIR/}"
    fi
done < <(find "$CACHE_DIR/$VERSION" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME" -type f -print0 2>/dev/null)

echo ""
echo "Installed: $INSTALL_PATH"
echo "Registered: $PLUGIN_KEY"
echo "Marketplace: $MARKETPLACE_DIR"
[ "$REPLACED" -gt 0 ] && echo "Token replaced in $REPLACED file(s)"
echo ""
echo "Done. Restart Claude Code to load the plugin."
