#!/usr/bin/env node
import { cpSync, rmSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');
const pluginSrc = join(projectRoot, 'src', 'plugin');
const assetsDir = join(projectRoot, 'cli', 'assets');

const dirs = ['skills', 'references', 'agents'];

for (const dir of dirs) {
  const dest = join(assetsDir, dir);
  rmSync(dest, { recursive: true, force: true });
  cpSync(join(pluginSrc, dir), dest, { recursive: true, dereference: true });
}

const templatesDest = join(assetsDir, 'templates', 'platforms');
rmSync(join(assetsDir, 'templates'), { recursive: true, force: true });
mkdirSync(templatesDest, { recursive: true });
cpSync(
  join(pluginSrc, 'templates', 'platforms'),
  templatesDest,
  { recursive: true }
);

console.log('Synced src/plugin/ -> cli/assets/');
