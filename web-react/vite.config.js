import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    // The survey-disc scene is isolated in a lazy chunk so the scientific
    // dashboard can render without waiting for the optional 3D dependency.
    chunkSizeWarningLimit: 850,
  },
});
