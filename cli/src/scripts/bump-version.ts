#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');

const bumpType = process.argv[2] || 'patch';
if (!['major', 'minor', 'patch'].includes(bumpType)) {
  console.error('Usage: bump-version [major|minor|patch]');
  process.exit(1);
}

const pyprojectPath = join(projectRoot, 'pyproject.toml');
const pyproject = readFileSync(pyprojectPath, 'utf-8');
const versionMatch = pyproject.match(/^version = "(.+)"/m);
if (!versionMatch) {
  console.error('Error: version not found in pyproject.toml');
  process.exit(1);
}

const oldVersion = versionMatch[1];
const [major, minor, patch] = oldVersion.split('.').map(Number);
let newVersion: string;

switch (bumpType) {
  case 'major': newVersion = `${major + 1}.0.0`; break;
  case 'minor': newVersion = `${major}.${minor + 1}.0`; break;
  default: newVersion = `${major}.${minor}.${patch + 1}`;
}

const filesToUpdate = [
  { path: pyprojectPath, pattern: `version = "${oldVersion}"`, replacement: `version = "${newVersion}"` },
  { path: join(projectRoot, 'src', 'claude_finance_kit', '__init__.py'), pattern: `__version__ = "${oldVersion}"`, replacement: `__version__ = "${newVersion}"` },
  { path: join(projectRoot, '.claude-plugin', 'plugin.json'), pattern: `"version": "${oldVersion}"`, replacement: `"version": "${newVersion}"` },
  { path: join(projectRoot, '.claude-plugin', 'marketplace.json'), pattern: `"version": "${oldVersion}"`, replacement: `"version": "${newVersion}"` },
  { path: join(projectRoot, 'cli', 'package.json'), pattern: `"version": "${oldVersion}"`, replacement: `"version": "${newVersion}"` },
];

for (const file of filesToUpdate) {
  try {
    const content = readFileSync(file.path, 'utf-8');
    const updated = content.replaceAll(file.pattern, file.replacement);
    if (content !== updated) {
      writeFileSync(file.path, updated);
    }
  } catch {
    // Skip files that don't exist
  }
}

console.log(`${oldVersion} -> ${newVersion}`);
