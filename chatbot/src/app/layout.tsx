import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/contexts/ThemeContext';

const inter = Inter({ subsets: ['latin'] });

/**
 * Metadatos de la aplicación
 * @description Chatbot Legal Municipal - Consultas de legislación BA
 */
export const metadata: Metadata = {
  title: {
    default: 'Asistente Legal Municipal',
    template: '%s | Asistente Legal Municipal',
  },
  description:
    'Chatbot especializado en legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina.',
  keywords: [
    'legislación municipal',
    'ordenanzas',
    'decretos',
    'Buenos Aires',
    'consulta legal',
    'municipios',
    'SIBOM',
  ],
  authors: [{ name: 'SIBOM Scraper Assistant' }],
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    siteName: 'Asistente Legal Municipal',
    title: 'Asistente Legal Municipal - Buenos Aires',
    description:
      'Consultá legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider defaultTheme="system">
          <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
