# claude-finance-kit-cli

CLI to install [claude-finance-kit](https://github.com/hongbietcode/claude-finance-kit) plugin for AI coding assistants.

Supports **Claude Code**, **Cursor**, and **GitHub Copilot**.

## Install

```bash
npx claude-finance-kit-cli init --ai claude    # Claude Code
npx claude-finance-kit-cli init --ai cursor    # Cursor
npx claude-finance-kit-cli init --ai copilot   # GitHub Copilot
npx claude-finance-kit-cli init                # Interactive (auto-detect)
```

## What Gets Installed

| Platform    | Skills | Agents | References |
| ----------- | ------ | ------ | ---------- |
| Claude Code | 4      | 4      | 9          |
| Cursor      | 4      | -      | 9          |
| Copilot     | 4      | -      | 9          |

**Skill:** finance-kit (orchestrator + all analysis workflows)

**Agents** (Claude only): fundamental-analyst, technical-analyst, macro-researcher, lead-analyst

## Prerequisites

```bash
pip install claude-finance-kit
```

Python >= 3.10 required. See [claude-finance-kit on PyPI](https://pypi.org/project/claude-finance-kit/).

## Commands

```bash
npx claude-finance-kit-cli init --ai <platform>       # Install plugin
npx claude-finance-kit-cli uninstall --ai <platform>   # Remove plugin
npx claude-finance-kit-cli --version                    # Show version
```

## Uninstall

```bash
npx claude-finance-kit-cli uninstall --ai claude
npx claude-finance-kit-cli uninstall --ai cursor
npx claude-finance-kit-cli uninstall --ai copilot
```

## License

MIT
