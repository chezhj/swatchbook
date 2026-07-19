import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [tailwindcss()],
  root: resolve(__dirname),
  base: '/static/dist/',
  build: {
    // Django serves this directory via STATICFILES_DIRS -> web/static/.
    outDir: resolve(__dirname, '../web/static/dist'),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(__dirname, 'src/main.js'),
    },
  },
  server: {
    port: 5173,
    // The "Vite: Stop Dev Server" task in .vscode/tasks.json kills this exact port.
    strictPort: true,
    origin: 'http://localhost:5173',
    // Django serves the page on :8800, so asset requests here are cross-origin.
    cors: true,
  },
});
