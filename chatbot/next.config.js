/** @type {import('next').NextConfig} */
const nextConfig = {
  /** @type {import('next').NextConfig} */
  reactStrictMode: true,
  
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
};

module.exports = nextConfig;
