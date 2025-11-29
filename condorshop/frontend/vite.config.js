import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // Code splitting: separar vendors en chunks para mejor caché y carga paralela
        manualChunks: {
          // React core (react, react-dom, react-router-dom) - chunk más grande pero raramente cambia
          'react-vendor': [
            'react',
            'react-dom',
            'react-router-dom'
          ],
          // Librerías de formularios (react-hook-form) - chunk mediano
          'form-vendor': [
            'react-hook-form'
          ],
          // Utilidades (axios, zustand) - chunk pequeño pero usado en todo el app
          'utils-vendor': [
            'axios',
            'zustand'
          ]
        },
        // Nombres de archivos para mejor debugging
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    // Optimización de chunks
    chunkSizeWarningLimit: 1000, // Aumentar límite de advertencia a 1MB
    // Minificación y optimización
    minify: 'esbuild',
    sourcemap: false, // Desactivar sourcemaps en producción para reducir tamaño
  }
})





