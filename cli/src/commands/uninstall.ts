import { readdir, rm } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';
import prompts from 'prompts';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { loadPlatformConfig } from '../utils/template.js';
import { logger } from '../utils/logger.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = join(__dirname, '..', '..', 'assets');

export interface UninstallOptions {
  ai?: AIType;
}

async function removeBundledEntries(sourceDir: string, destinationDir: string): Promise<void> {
  let entries;
  try {
    entries = await readdir(sourceDir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    await rm(join(destinationDir, entry.name), { recursive: entry.isDirectory(), force: true });
  }
}

export async function uninstallCommand(options: UninstallOptions): Promise<void> {
  logger.title('claude-finance-kit Uninstaller');

  let aiType = options.ai;

  if (!aiType) {
    const { detected, suggested } = detectAIType();

    if (detected.length > 0) {
      logger.info(`Detected: ${detected.map(t => chalk.cyan(t)).join(', ')}`);
    }

    const response = await prompts({
      type: 'select',
      name: 'aiType',
      message: 'Select AI assistant to uninstall from:',
      choices: AI_TYPES.map(type => ({
        title: getAITypeDescription(type),
        value: type,
      })),
      initial: suggested ? AI_TYPES.indexOf(suggested) : 0,
    });

    if (!response.aiType) {
      logger.warn('Uninstall cancelled');
      return;
    }

    aiType = response.aiType as AIType;
  }

  try {
    const config = await loadPlatformConfig(aiType);
    const cwd = process.cwd();
    const componentRoot = join(cwd, config.folderStructure.root);
    const skillDir = join(componentRoot, config.folderStructure.skillPath);

    const confirm = await prompts({
      type: 'confirm',
      name: 'proceed',
      message: `Remove claude-finance-kit files from ${chalk.red(skillDir)}?`,
      initial: false,
    });

    if (!confirm.proceed) {
      logger.warn('Uninstall cancelled');
      return;
    }

    if (config.components.skills) {
      await removeBundledEntries(join(ASSETS_DIR, 'skills'), skillDir);
    }

    if (config.components.references) {
      const refDir = join(componentRoot, 'references');
      await removeBundledEntries(join(ASSETS_DIR, 'references'), refDir);
    }
    if (config.components.agents) {
      const agentsDir = join(componentRoot, 'agents');
      await removeBundledEntries(join(ASSETS_DIR, 'agents'), agentsDir);
    }
    logger.success(`claude-finance-kit removed from ${getAITypeDescription(aiType)}`);
  } catch (error) {
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
