# Claude Desktop Project & Plugin Packaging Format

**Date:** 2026-04-01  
**Scope:** macOS `~/Library/Application Support/Claude/`, Projects feature, DXT plugin format

---

## 1. Claude Desktop "Projects" — How They Work

**Projects are fully server-side (claude.ai cloud).** No local filesystem representation exists.  
Data lives on Anthropic's servers, not in `~/Library/Application Support/Claude/`.

- **Custom instructions**: Free-text system prompt entered via UI → stored server-side
- **Knowledge files**: Uploaded via UI (PDF, DOCX, TXT, CSV, HTML, code files, up to 30MB/file, unlimited files) → stored server-side as RAG-indexed blobs
- **No import/export format**: No `.zip`, JSON schema, or local file to represent a Project
- **No public API**: Programmatic project creation via REST API does not exist (as of Q1 2026). Anthropic has referenced future API access but has not shipped it.

---

## 2. `~/Library/Application Support/Claude/` Directory Structure

Actual directories observed on this machine:

```
~/Library/Application Support/Claude/
├── claude_desktop_config.json          # MCP servers + UI preferences
├── config.json                         # OAuth token, theme, DXT allowlist cache
├── local-agent-mode-sessions/          # Claude Desktop "local agent" (Code) sessions
│   ├── <account-uuid>/
│   │   └── <session-uuid>/
│   │       ├── spaces.json             # Workspace → folder mappings (local only)
│   │       └── local_<uuid>.json       # Per-session metadata (title, model, CWD, etc.)
│   └── skills-plugin/
│       └── <account-uuid>/
│           └── <machine-uuid>/
│               ├── manifest.json       # Skills registry (skillId, description, enabled)
│               └── .claude-plugin/
│                   └── plugin.json     # Plugin identity (name, version, description)
├── bridge-state.json                   # Desktop bridge IPC state
└── extensions-installations.json      # Installed DXT extensions registry
```

**Key file formats:**

`claude_desktop_config.json` — MCP server registration:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": { "KEY": "value" }
    }
  },
  "preferences": { ... }
}
```

`spaces.json` — local workspace definition (no project instructions stored here):
```json
{
  "spaces": [{
    "id": "uuid", "name": "project-name",
    "folders": [{ "path": "/absolute/path" }],
    "projects": [], "links": []
  }]
}
```

---

## 3. DXT — The Only "Plugin" Format for Claude Desktop

DXT (Desktop Extensions) is the official packaging format for Claude Desktop plugins. It wraps an MCP server + metadata into a single `.dxt` file (ZIP).

**Toolchain:**
```bash
npm install -g @anthropic-ai/dxt
dxt init        # scaffold structure
dxt pack        # produce .dxt file
```

**Bundle structure:**
```
my-extension.dxt (ZIP)
├── manifest.json         # required
├── server/               # MCP server implementation
├── node_modules/         # bundled deps
├── icon.png              # optional
└── assets/               # optional reference docs
```

**`manifest.json` schema (v0.3):**
```json
{
  "manifest_version": "0.3",
  "name": "my-extension",
  "version": "1.0.0",
  "description": "...",
  "author": { "name": "...", "email": "..." },
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"],
      "env": { "API_KEY": "${user_config.api_key}" }
    }
  },
  "tools": [...],
  "prompts": [
    {
      "name": "analyze",
      "description": "...",
      "arguments": [...],
      "text": "You are a finance analyst. Context: ${documents}"
    }
  ],
  "user_config": {
    "api_key": { "type": "string", "description": "API key", "required": true }
  },
  "compatibility": {
    "platforms": ["darwin", "win32", "linux"]
  }
}
```

**DXT does NOT support:**
- Injecting system-level project instructions into Claude Desktop Projects
- Attaching knowledge files to a claude.ai Project
- Creating or modifying cloud Projects programmatically

DXT only bundles MCP tool servers — the system prompt and knowledge is delivered dynamically through MCP tool call responses, not pre-loaded into a Project.

---

## 4. Programmatic "Project with Instructions + Knowledge Files"

No direct path exists. Three workarounds ranked by practicality:

| Approach | How | Limitation |
|---|---|---|
| **MCP resource server** | DXT that serves files as MCP resources; instructions via tool schema | Requires user to trigger; no persistent project context |
| **CLAUDE.md injection** | Add `CLAUDE.md` + reference docs to workspace folder; Claude Code reads automatically | Only works in Claude Code (local agent), not claude.ai Projects |
| **claude.ai web UI (manual)** | Create project, paste instructions, upload files via browser | No automation possible today |

**For this project's use case** (packaging finance kit as a distributable "plugin" with instructions + reference docs):
- Best path: **CLAUDE.md + DXT MCP server** combo
  - `CLAUDE.md` = system instructions (auto-loaded by Claude Code)
  - DXT = bundles the MCP server that exposes finance kit tools
  - Reference docs = shipped in `assets/` inside DXT, served as MCP resources

---

## Sources
- [anthropics/dxt GitHub](https://github.com/anthropics/dxt) — official DXT toolchain
- [Claude Desktop Extensions overview](https://glama.ai/blog/2025-07-11-getting-started-with-mcp-desktop-extensions-dxt-in-claude-desktop)
- [What are projects — Claude Help Center](https://support.claude.com/en/articles/9517075-what-are-projects)
- [How to create and manage projects](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects)
- [DXT format explainer](https://dxt.so/posts/what-is-dxt)
- Local filesystem inspection: `~/Library/Application Support/Claude/` (this machine)

---

## Unresolved Questions

1. **Anthropic Projects API timeline**: No public commitment date for programmatic project creation via REST API. Watch `platform.claude.com` announcements.
2. **DXT `prompts` field delivery**: Unclear whether `prompts` in manifest.json pre-populate Claude Desktop's system prompt or are only user-invocable slash commands — needs hands-on testing.
3. **MCP resource protocol for knowledge files**: Whether MCP `resources` endpoint can effectively replicate "knowledge file" RAG behavior depends on server implementation quality — not guaranteed to match native project knowledge indexing.
