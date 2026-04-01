#!/usr/bin/env node
import { cpSync, rmSync, mkdirSync, readdirSync, lstatSync, copyFileSync, realpathSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');
const pluginSrc = join(projectRoot, 'plugin');
const assetsDir = join(projectRoot, 'cli', 'assets');

function copyDereferenced(src: string, dest: string): void {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    const stat = lstatSync(srcPath);
    if (stat.isSymbolicLink()) {
      const realPath = realpathSync(srcPath);
      const realStat = lstatSync(realPath);
      if (realStat.isDirectory()) {
        copyDereferenced(realPath, destPath);
      } else {
        copyFileSync(realPath, destPath);
      }
    } else if (stat.isDirectory()) {
      copyDereferenced(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

const dirs = ['skills', 'references', 'agents'];

for (const dir of dirs) {
  const dest = join(assetsDir, dir);
  rmSync(dest, { recursive: true, force: true });
  copyDereferenced(join(pluginSrc, dir), dest);
}

const templatesDest = join(assetsDir, 'templates', 'platforms');
rmSync(join(assetsDir, 'templates'), { recursive: true, force: true });
mkdirSync(templatesDest, { recursive: true });
cpSync(
  join(pluginSrc, 'templates', 'platforms'),
  templatesDest,
  { recursive: true }
);

console.log('Synced plugin/ -> cli/assets/');
