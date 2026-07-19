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
    strictPort: true,
    origin: 'http://localhost:5173',
  },
});
