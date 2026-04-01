#!/usr/bin/env node
import { readdir, lstat, readlink, unlink, copyFile, symlink, writeFile, readFile } from 'node:fs/promises';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = join(__dirname, '..', '..', 'assets');
const MANIFEST_PATH = join(ASSETS_DIR, '.symlink-manifest.json');

type SymlinkEntry = { path: string; target: string };

async function collectSymlinks(dir: string, entries: SymlinkEntry[] = []): Promise<SymlinkEntry[]> {
  const items = await readdir(dir);
  for (const item of items) {
    const fullPath = join(dir, item);
    const s = await lstat(fullPath);
    if (s.isDirectory()) {
      await collectSymlinks(fullPath, entries);
    } else if (s.isSymbolicLink()) {
      const target = await readlink(fullPath);
      entries.push({ path: fullPath.replace(ASSETS_DIR + '/', ''), target });
    }
  }
  return entries;
}

async function resolveSymlinks(): Promise<void> {
  console.log('prepack: resolving symlinks in assets/...');
  const entries = await collectSymlinks(ASSETS_DIR);
  if (entries.length === 0) {
    console.log('No symlinks found.');
    return;
  }

  await writeFile(MANIFEST_PATH, JSON.stringify(entries, null, 2));

  for (const entry of entries) {
    const fullPath = join(ASSETS_DIR, entry.path);
    const resolvedTarget = resolve(dirname(fullPath), entry.target);
    await unlink(fullPath);
    await copyFile(resolvedTarget, fullPath);
    console.log(`  resolved: ${entry.path}`);
  }
  console.log(`Done. Resolved ${entries.length} symlink(s).`);
}

async function restoreSymlinks(): Promise<void> {
  console.log('postpack: restoring symlinks in assets/...');
  let manifest: SymlinkEntry[];
  try {
    manifest = JSON.parse(await readFile(MANIFEST_PATH, 'utf-8'));
  } catch {
    console.log('No manifest found, skipping restore.');
    return;
  }

  for (const entry of manifest) {
    const fullPath = join(ASSETS_DIR, entry.path);
    await unlink(fullPath).catch(() => {});
    await symlink(entry.target, fullPath);
    console.log(`  restored: ${entry.path} -> ${entry.target}`);
  }

  await unlink(MANIFEST_PATH);
  console.log(`Done. Restored ${manifest.length} symlink(s).`);
}

const mode = process.argv[2];
if (mode === 'resolve') {
  await resolveSymlinks();
} else if (mode === 'restore') {
  await restoreSymlinks();
} else {
  console.error('Usage: resolve-symlinks [resolve|restore]');
  process.exit(1);
}
