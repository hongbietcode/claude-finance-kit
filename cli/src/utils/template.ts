import { readFile, writeFile, mkdir, cp, readdir, stat } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { PlatformConfig } from '../types/index.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = join(__dirname, '..', '..', 'assets');

export async function loadPlatformConfig(aiType: string): Promise<PlatformConfig> {
  const configPath = join(ASSETS_DIR, 'templates', 'platforms', `${aiType}.json`);
  const content = await readFile(configPath, 'utf-8');
  return JSON.parse(content) as PlatformConfig;
}

async function copyDir(src: string, dest: string): Promise<void> {
  await mkdir(dest, { recursive: true });
  await cp(src, dest, { recursive: true, dereference: true });
}

async function dirExists(path: string): Promise<boolean> {
  try {
    const s = await stat(path);
    return s.isDirectory();
  } catch {
    return false;
  }
}

async function rewriteRefPaths(dir: string, targetRelPath: string): Promise<void> {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      await rewriteRefPaths(fullPath, targetRelPath);
    } else if (entry.name.endsWith('.md')) {
      const content = await readFile(fullPath, 'utf-8');
      if (content.includes('../../references/')) {
        await writeFile(fullPath, content.replaceAll('../../references/', targetRelPath), 'utf-8');
      }
    }
  }
}

export async function generateForPlatform(
  targetDir: string,
  config: PlatformConfig
): Promise<string[]> {
  const createdFolders: string[] = [];
  const rootDir = join(targetDir, config.folderStructure.root);

  if (config.components.skills) {
    const skillsSrc = join(ASSETS_DIR, 'skills');
    if (await dirExists(skillsSrc)) {
      const skills = await readdir(skillsSrc);
      for (const skill of skills) {
        const skillSrc = join(skillsSrc, skill);
        const s = await stat(skillSrc);
        if (!s.isDirectory()) continue;

        const skillDest = join(rootDir, config.folderStructure.skillPath, skill);
        await copyDir(skillSrc, skillDest);
      }
      createdFolders.push(`${config.folderStructure.root}/${config.folderStructure.skillPath}/`);

      const depth = config.folderStructure.skillPath.split('/').length + 1;
      if (depth > 2) {
        const refRelPath = '../'.repeat(depth) + 'references/';
        const skillsDest = join(rootDir, config.folderStructure.skillPath);
        await rewriteRefPaths(skillsDest, refRelPath);
      }
    }
  }

  if (config.components.references) {
    const refSrc = join(ASSETS_DIR, 'references');
    if (await dirExists(refSrc)) {
      const refDest = join(rootDir, 'references');
      await copyDir(refSrc, refDest);
      createdFolders.push(`${config.folderStructure.root}/references/`);
    }
  }

  if (config.components.agents) {
    const agentsSrc = join(ASSETS_DIR, 'agents');
    if (await dirExists(agentsSrc)) {
      const agentsDest = join(rootDir, 'agents');
      await copyDir(agentsSrc, agentsDest);
      createdFolders.push(`${config.folderStructure.root}/agents/`);
    }
  }

  return createdFolders;
}
