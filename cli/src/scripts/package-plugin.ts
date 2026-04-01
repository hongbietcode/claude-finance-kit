import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';
import { createZipArchive } from '../utils/zip.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI_ROOT = join(__dirname, '..', '..');
const ASSETS_DIR = join(CLI_ROOT, 'assets');

async function main() {
  logger.title('claude-finance-kit Plugin Packager');

  const spinner = ora('Packaging plugin...').start();
  const pkg = JSON.parse(await readFile(join(CLI_ROOT, 'package.json'), 'utf-8'));

  try {
    const outputArg = process.argv[2];
    const outputPath = outputArg || join(CLI_ROOT, `claude-finance-kit-${pkg.version}.zip`);

    await createZipArchive(ASSETS_DIR, outputPath);

    spinner.succeed('Plugin packaged!');

    console.log();
    logger.info(`Output: ${chalk.cyan(outputPath)}`);
    logger.info(`Version: ${chalk.cyan(pkg.version)}`);

    console.log();
    logger.success('Plugin ZIP ready for distribution!');
    console.log();
    console.log(chalk.bold('Contents:'));
    console.log(chalk.dim('  .claude-plugin/ — plugin metadata'));
    console.log(chalk.dim('  agents/         — analyst agent definitions'));
    console.log(chalk.dim('  skills/         — stock-analysis, market-research, news-sentiment, marcus-vance'));
    console.log(chalk.dim('  references/     — API docs, methodology, patterns'));
    console.log(chalk.dim('  templates/      — platform configs (claude, cursor, copilot)'));
    console.log();
  } catch (error) {
    spinner.fail('Packaging failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}

main();
