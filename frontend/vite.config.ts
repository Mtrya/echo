import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  clearScreen: false,
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    strictPort: true,
    watch: {
      ignored: ['**/src-tauri/**']
    },
    proxy: {
      '^/(exams|session|health|audio_cache|api-key-status|settings|test-api|delete-exam|rename-exam|convert|voices).*': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
