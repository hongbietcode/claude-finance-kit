export type AIType = 'claude' | 'cursor' | 'copilot';

export const AI_TYPES: AIType[] = ['claude', 'cursor', 'copilot'];

export interface PlatformConfig {
  platform: string;
  displayName: string;
  folderStructure: {
    root: string;
    skillPath: string;
    filename: string;
  };
  components: {
    skills: boolean;
    references: boolean;
    agents: boolean;
    commands: boolean;
  };
  frontmatter: {
    format: string;
  };
  description: string;
}
