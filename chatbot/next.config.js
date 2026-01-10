/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

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
};

module.exports = nextConfig;
