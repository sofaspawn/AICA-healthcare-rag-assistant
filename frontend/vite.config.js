import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/patient': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
