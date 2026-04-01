import { readdir, readFile, stat, mkdir, writeFile, cp, rm } from 'node:fs/promises';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';
import chalk from 'chalk';
import ora from 'ora';
import { logger } from '../utils/logger.js';
import { createZipArchive } from '../utils/zip.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = join(__dirname, '..', '..', 'assets');

interface DxtManifest {
  manifest_version: string;
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  server: {
    type: string;
    entry_point: string;
  };
}

export interface PackageDxtOptions {
  output?: string;
}

async function collectAssetFiles(baseDir: string): Promise<{ relativePath: string; content: string }[]> {
  const files: { relativePath: string; content: string }[] = [];

  async function walk(dir: string): Promise<void> {
    const entries = await readdir(dir);
    for (const entry of entries) {
      const fullPath = join(dir, entry);
      const s = await stat(fullPath);
      if (s.isDirectory()) {
        await walk(fullPath);
      } else {
        const content = await readFile(fullPath, 'utf-8');
        const rel = relative(baseDir, fullPath);
        files.push({ relativePath: rel, content });
      }
    }
  }

  await walk(baseDir);
  return files;
}

function generateMcpServer(assetFiles: { relativePath: string; content: string }[]): string {
  const resourceEntries = assetFiles.map(f => ({
    uri: `finance-kit:///${f.relativePath}`,
    name: f.relativePath,
    mimeType: 'text/markdown',
  }));

  return `#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const RESOURCES = ${JSON.stringify(resourceEntries, null, 2)};

const RESOURCE_CONTENTS = ${JSON.stringify(
    Object.fromEntries(assetFiles.map(f => [f.relativePath, f.content])),
    null,
    2
  )};

const server = new Server(
  { name: "claude-finance-kit", version: "1.0.0" },
  { capabilities: { resources: { listChanged: false } } }
);

server.setRequestHandler(
  { method: "resources/list" },
  async () => ({ resources: RESOURCES })
);

server.setRequestHandler(
  { method: "resources/read" },
  async (request) => {
    const uri = request.params?.uri;
    const path = uri?.replace("finance-kit:///", "");
    const content = path ? RESOURCE_CONTENTS[path] : undefined;
    if (!content) {
      throw new Error("Resource not found: " + uri);
    }
    return {
      contents: [{ uri, mimeType: "text/markdown", text: content }],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
`;
}

export async function packageDxtCommand(options: PackageDxtOptions): Promise<void> {
  logger.title('claude-finance-kit DXT Packager');

  const spinner = ora('Collecting assets...').start();
  const pkg = JSON.parse(await readFile(join(__dirname, '..', '..', 'package.json'), 'utf-8'));

  try {
    const assetFiles = await collectAssetFiles(ASSETS_DIR);
    spinner.text = `Found ${assetFiles.length} asset files`;

    const buildDir = join(__dirname, '..', '..', '.dxt-build');
    await rm(buildDir, { recursive: true, force: true });
    await mkdir(join(buildDir, 'server'), { recursive: true });

    spinner.text = 'Generating MCP server...';
    const serverCode = generateMcpServer(assetFiles);
    await writeFile(join(buildDir, 'server', 'index.js'), serverCode);

    const serverPkg = {
      name: 'claude-finance-kit-mcp',
      version: pkg.version,
      type: 'module',
      dependencies: {
        '@modelcontextprotocol/sdk': '^1.0.0',
      },
    };
    await writeFile(join(buildDir, 'server', 'package.json'), JSON.stringify(serverPkg, null, 2));

    spinner.text = 'Creating manifest.json...';
    const manifest: DxtManifest = {
      manifest_version: '0.3',
      name: 'claude-finance-kit',
      version: pkg.version,
      description: 'Vietnamese stock market analysis toolkit — stock analysis, market research, technical analysis, fundamental analysis, macro research, news crawling.',
      author: 'hongbietcode',
      license: 'MIT',
      server: {
        type: 'node',
        entry_point: 'server/index.js',
      },
    };
    await writeFile(join(buildDir, 'manifest.json'), JSON.stringify(manifest, null, 2));

    spinner.text = 'Installing MCP server dependencies...';
    const { execSync } = await import('node:child_process');
    execSync('npm install --production', { cwd: join(buildDir, 'server'), stdio: 'ignore' });

    spinner.text = 'Packing .dxt archive...';
    const outputPath = options.output || join(process.cwd(), `claude-finance-kit-${pkg.version}.dxt`);
    await createZipArchive(buildDir, outputPath);

    await rm(buildDir, { recursive: true, force: true });

    spinner.succeed('DXT package created!');

    console.log();
    logger.info(`Output: ${chalk.cyan(outputPath)}`);
    logger.info(`Version: ${chalk.cyan(pkg.version)}`);
    logger.info(`Assets: ${chalk.cyan(String(assetFiles.length))} files bundled`);

    console.log();
    logger.success('Package ready for Claude Desktop!');
    console.log();
    console.log(chalk.bold('Install in Claude Desktop:'));
    console.log(chalk.dim('  1. Open Claude Desktop → Settings → Extensions'));
    console.log(chalk.dim('  2. Click "Install from file" and select the .dxt file'));
    console.log(chalk.dim(`  3. Or: double-click ${chalk.cyan(relative(process.cwd(), outputPath))}`));
    console.log();
  } catch (error) {
    spinner.fail('Packaging failed');
    if (error instanceof Error) {
      logger.error(error.message);
    }
    process.exit(1);
  }
}
