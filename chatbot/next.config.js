const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  /** Fix para warning de múltiples lockfiles */
  outputFileTracingRoot: path.join(__dirname, '..'),

  /** Configuración experimental */
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  /** Configuración de imágenes */
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

  /** Excluir directorios problemáticos del build */
  webpack: (config, { isServer }) => {
    // Ignorar venv de Python y otros directorios problemáticos
    config.watchOptions = {
      ...config.watchOptions,
      ignored: [
        '**/node_modules',
        '**/.git',
        '**/python-cli/venv/**',
        '**/python-cli/.venv/**',
        '**/python-cli/dist/**',
        '**/python-cli/boletines/**',
      ],
    };
    return config;
  },
};

module.exports = nextConfig;
