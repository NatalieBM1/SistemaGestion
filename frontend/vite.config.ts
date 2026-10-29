import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    // Aumentar el límite para evitar warnings que Render interpreta como error
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Separar las dependencias grandes en chunks propios
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          ui: ['lucide-react'],
        },
      },
    },
  },
})
