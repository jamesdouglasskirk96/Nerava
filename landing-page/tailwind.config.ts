import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1e40af', // EV blue
          dark: '#1e3a8a',
          light: '#3b82f6',
          soft: '#dbeafe',
        },
        secondary: {
          DEFAULT: '#64748b', // Soft gray
          light: '#94a3b8',
          dark: '#475569',
        },
      },
    },
  },
  plugins: [],
}
export default config

