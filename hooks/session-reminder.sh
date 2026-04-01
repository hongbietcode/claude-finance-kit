#!/bin/bash
# SessionStart hook — surfaces plugin capabilities to end-users
# Output: plain text reminder with operating principles, skills, agents, references, disclaimer
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

parse_frontmatter_field() {
  local file="$1" field="$2"
  sed -n '/^---$/,/^---$/p' "$file" | grep "^${field}:" | sed "s/^${field}:[[:space:]]*//" | head -1
}

echo "══════════════════════════════════════════════════════"
echo "  claude-finance-kit — Session Reminder"
echo "══════════════════════════════════════════════════════"
echo ""

echo "## Operating Principles"
echo "- Data-First: thesis → data → reasoning → conclusion. Never hallucinate."
echo "- No Bias: risk > reward → stay out. Setup unclear → no trade setup."
echo "- Concise & Actionable: bullets and data tables over paragraphs."
echo "- Real-Time Data Only: market indices MUST be fetched live, never fabricated."
echo ""

echo "## Skills (auto-invoked by context)"
if [ -d "$PLUGIN_ROOT/skills" ]; then
  for skill_dir in "$PLUGIN_ROOT"/skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    name=$(parse_frontmatter_field "$skill_dir/SKILL.md" "name")
    desc=$(parse_frontmatter_field "$skill_dir/SKILL.md" "description")
    [ -z "$name" ] && name=$(basename "$skill_dir")
    echo "- $name: $desc"
  done
fi
echo ""

echo "## Agents (specialized)"
if [ -d "$PLUGIN_ROOT/agents" ]; then
  for agent_file in "$PLUGIN_ROOT"/agents/*.md; do
    [ -f "$agent_file" ] || continue
    name=$(parse_frontmatter_field "$agent_file" "name")
    desc=$(parse_frontmatter_field "$agent_file" "description")
    [ -z "$name" ] && name=$(basename "$agent_file" .md)
    echo "- $name: $desc"
  done
fi
echo ""

echo "## References (load when needed)"
if [ -d "$PLUGIN_ROOT/references" ]; then
  for ref_file in "$PLUGIN_ROOT"/references/*.md; do
    [ -f "$ref_file" ] || continue
    echo "- $(basename "$ref_file")"
  done
fi
echo ""

echo "## Disclaimer"
echo "Reports are for reference only, not investment advice. You are responsible for your own capital allocation and risk management."
echo ""
echo "══════════════════════════════════════════════════════"
