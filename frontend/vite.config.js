import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '^/(exams|session|health|audio_cache|api-key-status|settings|test-api|delete-exam|rename-exam|convert).*': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})