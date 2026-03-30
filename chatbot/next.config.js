/** @type {import('next').NextConfig} */
const allowedDevOrigins = [
  'newly-welcome-glowworm.ngrok-free.app',
  ...(process.env.NEXT_ALLOWED_DEV_ORIGINS || '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean),
];

const nextConfig = {
  reactStrictMode: true,
  allowedDevOrigins,

  async redirects() {
    return [
      {
        source: '/satelite;',
        destination: '/satelite',
        permanent: false,
      },
      {
        source: '/satelite/:path*;',
        destination: '/satelite/:path*',
        permanent: false,
      },
    ];
  },

  /** Configuración experimental */
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },

  /** Configuración de Turbopack - silencia warning de lockfiles en directorios padre */
  turbopack: {
    root: __dirname,
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

  /** Output standalone para Docker */
  output: 'standalone',
};

module.exports = nextConfig;
