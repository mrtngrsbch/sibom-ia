const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  /** @type {import('next').NextConfig} */
  reactStrictMode: true,

  /** Fix para warning de múltiples lockfiles */
  outputFileTracingRoot: path.join(__dirname, '..', '..'),

  /** Configuración experimental si es necesaria */
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  /** Configuración de imágenes si se usa */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'sibom.slyt.gba.gob.ar',
      },
    ],
  },

  /** Transpile packages para compatibilidad con React 19 */
  transpilePackages: ['react-markdown', 'remark-gfm'],
};

module.exports = nextConfig;
