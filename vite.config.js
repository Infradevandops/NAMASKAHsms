import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  root: '.',
  base: '/static/',
  build: {
    outDir: 'static/dist',
    assetsDir: 'assets',
    minify: 'terser',
    sourcemap: true,
    rollupOptions: {
      input: {
        // Main entry points
        main: resolve(__dirname, 'static/js/main.js'),
        dashboard: resolve(__dirname, 'static/js/dashboard.js'),

        // Core modules
        constants: resolve(__dirname, 'static/js/constants.js'),
        'auth-helpers': resolve(__dirname, 'static/js/auth-helpers.ts'),
        'api-client': resolve(__dirname, 'static/js/api-client.js'),
        'api-retry': resolve(__dirname, 'static/js/api-retry.js'),

        // Components
        'tier-card': resolve(__dirname, 'static/js/tier-card.js'),
        'tier-manager': resolve(__dirname, 'static/js/tier-manager.js'),
        'dashboard-init': resolve(__dirname, 'static/js/dashboard-init.js'),
        'dashboard-loader': resolve(__dirname, 'static/js/dashboard-loader.js'),
        'frontend-logger': resolve(__dirname, 'static/js/frontend-logger.js'),
        'auth-store': resolve(__dirname, 'static/js/store/auth-store.js'),
      },
      output: {
        entryFileNames: 'js/[name].[hash].js',
        chunkFileNames: 'js/chunks/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/png|jpe?g|gif|svg|webp|ico/.test(ext)) {
            return `images/[name].[hash][extname]`
          } else if (/woff|woff2|eot|ttf|otf/.test(ext)) {
            return `fonts/[name].[hash][extname]`
          } else if (ext === 'css') {
            return `css/[name].[hash][extname]`
          }
          return `[name].[hash][extname]`
        },
        // Shared chunks for common dependencies
        manualChunks: {
          'vendor-constants': ['./static/js/constants.js'],
          'vendor-auth': ['./static/js/auth-helpers.js'],
        }
      }
    },
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true
      }
    }
  },
  server: {
    middlewareMode: true,
    hmr: {
      host: 'localhost',
      port: 5173
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'static/js'),
      '@store': resolve(__dirname, 'static/js/store'),
      '@css': resolve(__dirname, 'static/css')
    }
  }
})
