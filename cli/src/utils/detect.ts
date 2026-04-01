import { existsSync } from 'node:fs';
import { join } from 'node:path';
import type { AIType } from '../types/index.js';

interface DetectionResult {
  detected: AIType[];
  suggested: AIType | null;
}

export function detectAIType(cwd: string = process.cwd()): DetectionResult {
  const detected: AIType[] = [];

  if (existsSync(join(cwd, '.claude'))) detected.push('claude');
  if (existsSync(join(cwd, '.cursor'))) detected.push('cursor');
  if (existsSync(join(cwd, '.github'))) detected.push('copilot');

  let suggested: AIType | null = null;
  if (detected.length === 1) {
    suggested = detected[0];
  }

  return { detected, suggested };
}

export function getAITypeDescription(aiType: AIType): string {
  switch (aiType) {
    case 'claude':
      return 'Claude Code (.claude/)';
    case 'cursor':
      return 'Cursor (.cursor/rules/)';
    case 'copilot':
      return 'GitHub Copilot (.github/prompts/)';
  }
}
