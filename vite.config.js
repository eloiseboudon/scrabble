import vue from '@vitejs/plugin-vue'
import path from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
    plugins: [vue()],
    root: './frontend',
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './frontend')
        }
    },
    server: {
        port: 5173
    }
})