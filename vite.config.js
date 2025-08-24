import vue from '@vitejs/plugin-vue'
import path from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  root: './frontend',
  publicDir: 'public',
  assetsInclude: ['**/*.js'],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './frontend')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '^/api/.*': { target: 'http://localhost:8000', changeOrigin: true },
      '^/(api|auth|games|uploads)$': { target: 'http://localhost:8000', changeOrigin: true },
      '^/(validate|finish|health|docs|redoc|openapi\\.json)$': { target: 'http://localhost:8000', changeOrigin: true },
      '^/games/.*': { target: 'http://localhost:8000', changeOrigin: true },
      '^/auth/.*': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  optimizeDeps: {
    include: ['vue', 'vue-router']
  },
  build: {
    outDir: '../dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'frontend/index.html')
      }
    }
  }
})