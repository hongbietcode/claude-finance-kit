import { readdir, readFile, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { execSync } from 'node:child_process';

export async function createZipArchive(sourceDir: string, outputPath: string): Promise<void> {
  execSync(`cd "${sourceDir}" && zip -r "${outputPath}" .`, { stdio: 'ignore' });
}
