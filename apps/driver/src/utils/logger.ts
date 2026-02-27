const isDev = import.meta.env.DEV

export const logger = {
  log: (...args: unknown[]) => { if (isDev) console.log(...args) },
  warn: (...args: unknown[]) => { if (isDev) console.warn(...args) },
  error: (...args: unknown[]) => console.error(...args), // always log errors
  debug: (...args: unknown[]) => { if (isDev) console.debug(...args) },
  group: (...args: unknown[]) => { if (isDev) console.group(...args) },
  groupEnd: () => { if (isDev) console.groupEnd() },
}
