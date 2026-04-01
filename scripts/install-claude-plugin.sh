#!/bin/bash
# Download and install claude-finance-kit plugin
# Usage: GITHUB_TOKEN=ghp_xxx bash scripts/install-claude-plugin.sh [version]
set -e

REPO="hongbietcode/claude-finance-kit"
MARKETPLACE="hongbietcode-claude-finance-kit"
PLUGIN_NAME="claude-finance-kit"

MODE=""
PROJECT_DIR=""
TAG="$1"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN env var required"
    echo "Usage: GITHUB_TOKEN=ghp_xxx bash $0 [version]"
    exit 1
fi

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
DIM="\033[2m"
RESET="\033[0m"

printf "\n"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
printf "${BOLD}${CYAN}    claude-finance-kit — Select Install Scope${RESET}\n"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
printf "\n"
printf "  ${BOLD}1)${RESET} ${GREEN}User${RESET}     — install to ${DIM}~/.claude/${RESET} (available in all projects)\n"
printf "  ${BOLD}2)${RESET} ${YELLOW}Project${RESET}  — install to ${DIM}.claude/${RESET} in current directory only\n"
printf "\n"
printf "  Enter choice [1/2]: "
read -r CHOICE </dev/tty

case "$CHOICE" in
    2)
        MODE="project"
        printf "\n  Project directory [$(pwd)]: "
        read -r INPUT_DIR </dev/tty
        PROJECT_DIR="${INPUT_DIR:-$(pwd)}"
        ;;
    *)
        MODE="user"
        ;;
esac
printf "\n"

if [ -z "$TAG" ] && [ -n "$1" ] && [[ "$1" == v*.*.* ]]; then
    TAG="$1"
fi

if [ -z "$TAG" ]; then
    TAG=$(curl -fsSL \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO/releases/latest" \
        | grep '"tag_name"' | sed 's/.*: "\(.*\)".*/\1/')
    if [ -z "$TAG" ]; then
        echo "Error: could not fetch latest release. Pass version manually: $0 v0.1.9"
        exit 1
    fi
fi

VERSION="${TAG#v}"
ZIP_NAME="${PLUGIN_NAME}-plugin-${TAG}.zip"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

if [ "$MODE" = "project" ]; then
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$(pwd)"
    fi
    CLAUDE_DIR="$PROJECT_DIR/.claude"
    INSTALL_PATH="$CLAUDE_DIR"
else
    CLAUDE_DIR="$HOME/.claude"
    MARKETPLACE_DIR="$CLAUDE_DIR/plugins/marketplaces/$MARKETPLACE"
    CACHE_DIR="$CLAUDE_DIR/plugins/cache/$MARKETPLACE/$PLUGIN_NAME"
    REGISTRY="$CLAUDE_DIR/plugins/installed_plugins.json"
    MARKETPLACES="$CLAUDE_DIR/plugins/known_marketplaces.json"
    INSTALL_PATH="$CACHE_DIR/$VERSION"
fi

echo "Installing $PLUGIN_NAME plugin $TAG (scope: $MODE)..."

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

GIT_SHA=$(curl -fsSL \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/git/ref/tags/$TAG" \
    | grep '"sha"' | head -1 | sed 's/.*"\([a-f0-9]\{40\}\)".*/\1/')

if [ "$MODE" = "project" ]; then
    mkdir -p "$INSTALL_PATH"
    unzip -qo "$TMP_DIR/$ZIP_NAME" -d "$TMP_DIR/extracted"

    for dir in skills agents references docs .claude-plugin; do
        [ -d "$TMP_DIR/extracted/$dir" ] && cp -r "$TMP_DIR/extracted/$dir" "$INSTALL_PATH/"
    done

    [ -f "$TMP_DIR/extracted/CLAUDE.md" ] && cp "$TMP_DIR/extracted/CLAUDE.md" "$INSTALL_PATH/CLAUDE.md"

else
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
    for dir in skills agents references docs; do
        [ -d "$CACHE_DIR/$VERSION/$dir" ] && cp -r "$CACHE_DIR/$VERSION/$dir" "$MARKETPLACE_DIR/plugins/$PLUGIN_NAME/"
    done

    NOW=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
    PLUGIN_KEY="${PLUGIN_NAME}@${MARKETPLACE}"

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
    'source': {'source': 'github', 'repo': '$REPO'},
    'installLocation': '$MARKETPLACE_DIR',
    'lastUpdated': '$NOW'
}
json.dump(mkts, open(marketplaces_path, 'w'), indent=2)
"
fi

TOKEN_B64=$(echo -n "$GITHUB_TOKEN" | base64)
REPLACED=0
while IFS= read -r -d '' file; do
    if grep -q '<YOUR_BASE64_ENCODED_GITHUB_TOKEN>' "$file" 2>/dev/null; then
        sed -i '' "s|<YOUR_BASE64_ENCODED_GITHUB_TOKEN>|$TOKEN_B64|g" "$file"
        REPLACED=$((REPLACED + 1))
    fi
done < <(find "$INSTALL_PATH" -type f -print0 2>/dev/null)

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
DIM="\033[2m"
RESET="\033[0m"

mapfile -t SKILLS < <(find "$INSTALL_PATH/skills" -name "SKILL.md" -maxdepth 2 2>/dev/null | while read -r f; do basename "$(dirname "$f")"; done | sort)
mapfile -t AGENTS < <(find "$INSTALL_PATH/agents" -name "*.md" -maxdepth 1 2>/dev/null | while read -r f; do basename "$f" .md; done | sort)

COL1=24
COL2=44

print_border_top() { printf "  ${DIM}┌"; printf '─%.0s' $(seq 1 $((COL1+2))); printf '┬'; printf '─%.0s' $(seq 1 $((COL2+2))); printf "┐${RESET}\n"; }
print_border_mid() { printf "  ${DIM}├"; printf '─%.0s' $(seq 1 $((COL1+2))); printf '┼'; printf '─%.0s' $(seq 1 $((COL2+2))); printf "┤${RESET}\n"; }
print_border_bot() { printf "  ${DIM}└"; printf '─%.0s' $(seq 1 $((COL1+2))); printf '┴'; printf '─%.0s' $(seq 1 $((COL2+2))); printf "┘${RESET}\n"; }
print_header_row() {
    printf "  ${DIM}│${RESET} ${BOLD}${CYAN}%-*s${RESET} ${DIM}│${RESET} ${BOLD}${CYAN}%-*s${RESET} ${DIM}│${RESET}\n" "$COL1" "$1" "$COL2" "$2"
}
print_row() {
    local color="$1" c1="$2" c2="$3"
    while [ ${#c2} -gt $COL2 ]; do
        printf "  ${DIM}│${RESET} ${color}%-*s${RESET} ${DIM}│${RESET} %-*s ${DIM}│${RESET}\n" "$COL1" "$c1" "$COL2" "${c2:0:$COL2}"
        c1=""
        c2="${c2:$COL2}"
    done
    printf "  ${DIM}│${RESET} ${color}%-*s${RESET} ${DIM}│${RESET} %-*s ${DIM}│${RESET}\n" "$COL1" "$c1" "$COL2" "$c2"
}

SCOPE_LABEL="user (~/.claude)"
[ "$MODE" = "project" ] && SCOPE_LABEL="project ($PROJECT_DIR/.claude)"

printf "\n"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
printf "${BOLD}${CYAN}    claude-finance-kit %s — Installation Complete${RESET}\n" "$TAG"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
printf "\n"
printf "  ${BOLD}%-12s${RESET} ${GREEN}%s${RESET}\n"  "Version:"  "$VERSION"
printf "  ${BOLD}%-12s${RESET} %s\n"                   "Scope:"    "$SCOPE_LABEL"
printf "  ${BOLD}%-12s${RESET} ${DIM}%s${RESET}\n"     "Path:"     "$INSTALL_PATH"
[ "$REPLACED" -gt 0 ] && printf "  ${BOLD}%-12s${RESET} ${YELLOW}Replaced in %s file(s)${RESET}\n" "Token:" "$REPLACED"
printf "\n"

printf "  ${BOLD}Skills${RESET}\n"
print_border_top
print_header_row "Name" "Description"
print_border_mid
if [ "${#SKILLS[@]}" -gt 0 ]; then
    for s in "${SKILLS[@]}"; do
        DESC=$(head -10 "$INSTALL_PATH/skills/$s/SKILL.md" 2>/dev/null | grep -m1 "^[^#*-]" | sed 's/^[[:space:]]*//')
        [ -z "$DESC" ] && DESC=$(echo "$s" | sed 's/-/ /g')
        print_row "$GREEN" "$s" "$DESC"
    done
else
    print_row "" "(none)" ""
fi
print_border_bot

printf "\n"
printf "  ${BOLD}Agents${RESET}\n"
print_border_top
print_header_row "Name" "Role"
print_border_mid
if [ "${#AGENTS[@]}" -gt 0 ]; then
    for a in "${AGENTS[@]}"; do
        ROLE=$(grep -m1 "^[^#*-]" "$INSTALL_PATH/agents/$a.md" 2>/dev/null | sed 's/^[[:space:]]*//')
        [ -z "$ROLE" ] && ROLE=$(echo "$a" | sed 's/-/ /g')
        print_row "$YELLOW" "$a" "$ROLE"
    done
else
    print_row "" "(none)" ""
fi
print_border_bot

printf "\n"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
[ "$MODE" = "user" ] && printf "    Restart Claude Code to load the plugin.\n"
[ "$MODE" = "project" ] && printf "    Open project in Claude Code to load the plugin.\n"
printf "${BOLD}${CYAN}  ══════════════════════════════════════════════════════════════════${RESET}\n"
