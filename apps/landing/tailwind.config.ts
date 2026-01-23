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
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: {
          DEFAULT: '#2952E8',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#f5f5f5',
          foreground: '#1a1a1a',
        },
        muted: {
          DEFAULT: '#6b6b6b',
          foreground: '#6b6b6b',
        },
        accent: {
          DEFAULT: '#e9ebef',
          foreground: '#030213',
        },
        destructive: {
          DEFAULT: '#d4183d',
          foreground: '#ffffff',
        },
        border: '#e5e5e5',
        card: {
          DEFAULT: '#ffffff',
          foreground: '#1a1a1a',
        },
        input: 'transparent',
        'input-background': '#f3f3f5',
        ring: 'oklch(0.708 0 0)',
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        sm: 'calc(0.5rem - 4px)',
        md: 'calc(0.5rem - 2px)',
        lg: '0.5rem',
        xl: 'calc(0.5rem + 4px)',
      },
    },
  },
  plugins: [],
}
export default config

