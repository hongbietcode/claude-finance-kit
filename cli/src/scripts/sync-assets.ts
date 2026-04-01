#!/usr/bin/env node
import { rmSync, readdirSync, lstatSync, readlinkSync, symlinkSync, mkdirSync, copyFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');
const pluginSrc = join(projectRoot, 'plugin');
const assetsDir = join(projectRoot, 'cli', 'assets');

function copyPreservingSymlinks(src: string, dest: string): void {
  mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    const stat = lstatSync(srcPath);
    if (stat.isSymbolicLink()) {
      symlinkSync(readlinkSync(srcPath), destPath);
    } else if (stat.isDirectory()) {
      copyPreservingSymlinks(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

rmSync(assetsDir, { recursive: true, force: true });
copyPreservingSymlinks(pluginSrc, assetsDir);

console.log('Synced plugin/ -> cli/assets/');
