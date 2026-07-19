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
    // Bind all interfaces, not just localhost -- dev.py binds Django to 0.0.0.0 so the
    // app can be opened on a phone over the LAN, and the dev server needs to be
    // reachable there too.
    host: true,
    // No fixed origin: leaving it unset makes Vite resolve asset/HMR URLs relative to
    // whatever host:port the browser actually requested this server from, so the same
    // config works for localhost, 127.0.0.1, and a LAN IP without picking one upfront.
    // Single-user, LAN-only dev server -- skip Vite's Host-header allowlist so it
    // answers regardless of which hostname/IP the request came in on.
    allowedHosts: true,
    // Django serves the page on :8800, so asset requests here are cross-origin.
    cors: true,
  },
}));
