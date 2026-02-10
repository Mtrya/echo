import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  clearScreen: false,
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
