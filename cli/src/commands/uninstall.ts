import { rm } from 'node:fs/promises';
import { join } from 'node:path';
import chalk from 'chalk';
import prompts from 'prompts';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { loadPlatformConfig } from '../utils/template.js';
import { logger } from '../utils/logger.js';

export interface UninstallOptions {
  ai?: AIType;
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
    const skillDir = join(cwd, config.folderStructure.root, config.folderStructure.skillPath);

    const confirm = await prompts({
      type: 'confirm',
      name: 'proceed',
      message: `Remove ${chalk.red(skillDir)}?`,
      initial: false,
    });

    if (!confirm.proceed) {
      logger.warn('Uninstall cancelled');
      return;
    }

    await rm(skillDir, { recursive: true, force: true });

    if (config.components.references) {
      const refDir = join(cwd, config.folderStructure.root, 'references');
      await rm(refDir, { recursive: true, force: true });
    }
    if (config.components.agents) {
      const agentsDir = join(cwd, config.folderStructure.root, 'agents');
      await rm(agentsDir, { recursive: true, force: true });
    }
    if (config.components.commands) {
      const cmdsDir = join(cwd, config.folderStructure.root, 'commands');
      await rm(cmdsDir, { recursive: true, force: true });
    }

    logger.success(`claude-finance-kit removed from ${getAITypeDescription(aiType)}`);
  } catch (error) {
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
