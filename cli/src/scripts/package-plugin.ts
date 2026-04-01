#!/usr/bin/env node
import { execSync } from 'node:child_process';
import { readFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');
const pyprojectPath = join(projectRoot, 'pyproject.toml');
const pyproject = readFileSync(pyprojectPath, 'utf-8');

const versionMatch = pyproject.match(/^version = "(.+)"/m);
if (!versionMatch) {
  console.error('Error: version not found in pyproject.toml');
  process.exit(1);
}
const version = versionMatch[1];
const skillName = 'claude-finance-kit';
const distDir = join(projectRoot, 'dist');
const output = join(distDir, `${skillName}-plugin-v${version}.zip`);

mkdirSync(distDir, { recursive: true });
if (existsSync(output)) rmSync(output);

console.log(`Packaging ${skillName} plugin v${version}...`);

execSync(
  `zip -r9 "${output}" ` +
  `".claude-plugin/" ` +
  `"src/plugin/skills/" ` +
  `"src/plugin/references/" ` +
  `"src/plugin/agents/" ` +
  `"docs/" ` +
  `"CLAUDE.md" ` +
  `-x "*.DS_Store"`,
  { cwd: projectRoot, stdio: 'inherit' }
);

const stat = readFileSync(output);
const sizeKB = Math.round(stat.length / 1024);
console.log(`\nDone: ${output}`);
console.log(`Size: ${sizeKB}KB`);
