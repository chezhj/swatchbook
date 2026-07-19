import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'path';

export default defineConfig(({ command }) => ({
  plugins: [tailwindcss()],
  root: resolve(__dirname),

  // `base` applies to the dev server as well as the build. Serving dev from the root
  // keeps the URL that {% vite_asset %} emits simple (http://localhost:5173/src/main.js);
  // builds still need /static/dist/ so asset references inside the bundled CSS resolve
  // through Django's staticfiles.
  base: command === 'serve' ? '/' : '/static/dist/',

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
}));
