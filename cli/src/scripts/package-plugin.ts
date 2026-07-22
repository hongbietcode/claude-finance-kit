import { readFile, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';
import { createZipArchive } from '../utils/zip.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI_ROOT = join(__dirname, '..', '..');
const ASSETS_DIR = join(CLI_ROOT, 'assets');

async function syncManifestVersion(manifestPath: string, version: string): Promise<void> {
  const content = await readFile(manifestPath, 'utf-8');
  const manifest = JSON.parse(content);
  if (manifest.version === version) return;

  const updated = content.replace(/("version"\s*:\s*")[^"]+("\s*[,}])/, `$1${version}$2`);
  if (updated === content) {
    throw new Error(`Could not update plugin version in ${manifestPath}`);
  }
  await writeFile(manifestPath, updated, 'utf-8');
}

async function main() {
  logger.title('claude-finance-kit Multi-Platform Plugin Packager');

  const spinner = ora('Packaging plugin...').start();
  const pkg = JSON.parse(await readFile(join(CLI_ROOT, 'package.json'), 'utf-8'));

  try {
    await Promise.all([
      syncManifestVersion(join(ASSETS_DIR, '.claude-plugin', 'plugin.json'), pkg.version),
      syncManifestVersion(join(ASSETS_DIR, '.codex-plugin', 'plugin.json'), pkg.version),
    ]);

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
    console.log(chalk.dim('  .claude-plugin/          — plugin metadata'));
    console.log(chalk.dim('  .codex-plugin/           — Codex plugin manifest'));
    console.log(chalk.dim('  agents/                  — fundamental, technical, macro, lead'));
    console.log(chalk.dim('  skills/finance-kit/   — skill + references + scripts'));
    console.log(chalk.dim('  templates/               — platform configs (claude, codex, cursor, copilot)'));
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
