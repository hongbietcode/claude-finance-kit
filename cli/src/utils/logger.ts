import chalk from 'chalk';

export const logger = {
  title(msg: string) {
    console.log();
    console.log(chalk.bold.cyan(`  ${msg}`));
    console.log(chalk.dim('  ' + '─'.repeat(50)));
    console.log();
  },
  info(msg: string) {
    console.log(`  ${chalk.blue('ℹ')} ${msg}`);
  },
  success(msg: string) {
    console.log(`  ${chalk.green('✔')} ${msg}`);
  },
  warn(msg: string) {
    console.log(`  ${chalk.yellow('⚠')} ${msg}`);
  },
  error(msg: string) {
    console.log(`  ${chalk.red('✖')} ${msg}`);
  },
};
