import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // GitHub Pages serves this app at https://<username>.github.io/quickrx/
  // so all asset paths must be prefixed with /quickrx/. Change this if you
  // rename the repo.
  base: "/quickrx/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
