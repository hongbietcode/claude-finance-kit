import chalk from 'chalk';
import ora from 'ora';
import prompts from 'prompts';
import type { AIType } from '../types/index.js';
import { AI_TYPES } from '../types/index.js';
import { detectAIType, getAITypeDescription } from '../utils/detect.js';
import { loadPlatformConfig, generateForPlatform } from '../utils/template.js';
import { logger } from '../utils/logger.js';

export interface InitOptions {
  ai?: AIType;
  force?: boolean;
}

export async function initCommand(options: InitOptions): Promise<void> {
  logger.title('claude-finance-kit Installer');

  let aiType = options.ai;

  if (!aiType) {
    const { detected, suggested } = detectAIType();

    if (detected.length > 0) {
      logger.info(`Detected: ${detected.map(t => chalk.cyan(t)).join(', ')}`);
    }

    const response = await prompts({
      type: 'select',
      name: 'aiType',
      message: 'Select AI assistant to install for:',
      choices: AI_TYPES.map(type => ({
        title: getAITypeDescription(type),
        value: type,
      })),
      initial: suggested ? AI_TYPES.indexOf(suggested) : 0,
    });

    if (!response.aiType) {
      logger.warn('Installation cancelled');
      return;
    }

    aiType = response.aiType as AIType;
  }

  logger.info(`Installing for: ${chalk.cyan(getAITypeDescription(aiType))}`);

  const spinner = ora('Installing files...').start();
  const cwd = process.cwd();

  try {
    const config = await loadPlatformConfig(aiType);
    spinner.text = 'Generating plugin files...';
    const createdFolders = await generateForPlatform(cwd, config);
    spinner.succeed('Plugin installed!');

    console.log();
    logger.info('Installed:');
    createdFolders.forEach(folder => {
      console.log(`  ${chalk.green('+')} ${folder}`);
    });

    console.log();
    logger.success('claude-finance-kit installed successfully!');

    console.log();
    console.log(chalk.bold('Prerequisites:'));
    console.log(chalk.dim('  pip install claude-finance-kit'));
    console.log();
    console.log(chalk.bold('Next steps:'));
    console.log(chalk.dim('  1. Restart your AI coding assistant'));
    console.log(chalk.dim('  2. Try: "Analyze FPT stock"'));
    console.log();
  } catch (error) {
    spinner.fail('Installation failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
