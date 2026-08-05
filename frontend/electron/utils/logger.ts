import log from 'electron-log';

log.transports.file.level = 'info';
log.transports.console.level = 'debug';

export const logger = {
  info: (msg: string, ...args: any[]) => log.info(msg, ...args),
  warn: (msg: string, ...args: any[]) => log.warn(msg, ...args),
  error: (msg: string, ...args: any[]) => log.error(msg, ...args),
  debug: (msg: string, ...args: any[]) => log.debug(msg, ...args),
};
