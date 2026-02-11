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
    default: 'Mangrullo — Observatorio independiente de la decepción municipal',
    template: '%s | Mangrullo',
  },
  description:
    'Observatorio independiente de legislación municipal. Consultá ordenanzas, decretos y tasas de los 135 municipios de la Provincia de Buenos Aires.',
  keywords: [
    'mangrullo',
    'legislación municipal',
    'ordenanzas',
    'decretos',
    'tasas municipales',
    'transparencia',
    'Buenos Aires',
    'municipios',
    'SIBOM',
  ],
  authors: [{ name: 'Mangrullo' }],
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    siteName: 'Mangrullo',
    title: 'Mangrullo — Observatorio independiente de la decepción municipal',
    description:
      'Consultá legislación, ordenanzas y tasas de los municipios de la Provincia de Buenos Aires.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const theme = localStorage.getItem('theme-preference') || 'system';
                const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                if (isDark) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              })();
            `,
          }}
        />
      </head>
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
