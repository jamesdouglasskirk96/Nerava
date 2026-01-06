import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = process.env.VITE_ENV || mode
  
  // Build-time check: fail if API URL is invalid in production
  if (env === 'prod' || env === 'production') {
    const apiBaseUrl = process.env.VITE_API_BASE_URL || ''
    if (apiBaseUrl === '/api' || apiBaseUrl.startsWith('http://localhost')) {
      throw new Error(
        `VITE_API_BASE_URL cannot be '/api' or 'http://localhost:*' in production builds. ` +
        `Current value: ${apiBaseUrl}. ` +
        `Set VITE_API_BASE_URL to your production API URL (e.g., https://api.nerava.network)`
      )
    }
  }
  
  return {
    base: process.env.VITE_PUBLIC_BASE || '/',
    plugins: [react()],
    server: {
      port: 3001,
      proxy: {
        '/v1': {
          target: 'http://localhost:8001',
          changeOrigin: true,
        },
      },
    },
  }
})







