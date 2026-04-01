#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..', '..', '..');
const pyprojectPath = join(projectRoot, 'pyproject.toml');
const content = readFileSync(pyprojectPath, 'utf-8');

const lines: string[] = [];

const coreDepsMatch = content.match(/^dependencies = \[\n([\s\S]*?)\n\]/m);
if (coreDepsMatch) {
  lines.push('# Core dependencies');
  const deps = coreDepsMatch[1].match(/"([^"]+)"/g);
  if (deps) {
    for (const dep of deps) {
      lines.push(dep.replace(/"/g, ''));
    }
  }
}

const optionalSection = content.match(/\[project\.optional-dependencies\]\n([\s\S]*?)(?=\n\[|$)/);
if (optionalSection) {
  const block = optionalSection[1];
  const extraRegex = /^(\w[\w-]*) = \[\n([\s\S]*?)\n\]/gm;
  let match;
  while ((match = extraRegex.exec(block)) !== null) {
    const extraName = match[1];
    const depBlock = match[2];
    const deps = depBlock.match(/"([^"]+)"/g);
    if (deps && deps.length > 0 && !deps[0].includes('claude-finance-kit')) {
      lines.push('');
      lines.push(`# Extra: ${extraName}`);
      for (const dep of deps) {
        lines.push(dep.replace(/"/g, ''));
      }
    }
  }
}

console.log(lines.join('\n'));
