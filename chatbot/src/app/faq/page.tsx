'use client';

import { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink } from '@/lib/icons';

/**
 * Página de Preguntas Frecuentes (FAQ)
 * @description Muestra información útil sobre cómo usar el chatbot
 */
export default function FAQPage() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [markdownContent, setMarkdownContent] = useState('');

  useEffect(() => {
    // Cargar contenido del FAQ desde el endpoint
    fetch('/api/faq-content')
      .then(res => res.text())
      .then(content => setMarkdownContent(content))
      .catch(error => {
        console.error('Error cargando FAQ:', error);
        setMarkdownContent('# Error\n\nNo se pudo cargar el contenido del FAQ.');
      });
  }, []);

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <Header onMenuClick={() => setIsDrawerOpen(true)} />

      {/* Layout principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Contenido principal */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto p-6 sm:p-8">
            <article className="prose prose-slate dark:prose-invert max-w-none prose-headings:text-slate-800 dark:prose-headings:text-slate-200 prose-p:text-slate-700 dark:prose-p:text-slate-300 prose-strong:text-slate-800 dark:prose-strong:text-slate-200 prose-li:text-slate-700 dark:prose-li:text-slate-300 prose-a:text-primary-600 dark:prose-a:text-primary-400 prose-code:text-slate-800 dark:prose-code:text-slate-200 prose-pre:bg-slate-800 dark:prose-pre:bg-slate-900">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Enlaces externos con ícono
                  a: ({ node, ...props }) => {
                    const isExternal = props.href?.startsWith('http');
                    return (
                      <a
                        {...props}
                        target={isExternal ? '_blank' : undefined}
                        rel={isExternal ? 'noopener noreferrer' : undefined}
                        className="inline-flex items-center gap-1"
                      >
                        {props.children}
                        {isExternal && <ExternalLink className="w-3 h-3" />}
                      </a>
                    );
                  },
                  // Tablas estilizadas
                  table: ({ node, ...props }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg" {...props} />
                    </div>
                  ),
                  thead: ({ node, ...props }) => (
                    <thead className="bg-slate-100 dark:bg-slate-800" {...props} />
                  ),
                  tbody: ({ node, ...props }) => (
                    <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700" {...props} />
                  ),
                  tr: ({ node, ...props }) => (
                    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors" {...props} />
                  ),
                  th: ({ node, ...props }) => (
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider" {...props} />
                  ),
                  td: ({ node, ...props }) => (
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400" {...props} />
                  ),
                  // Bloques de código
                  code: ({ node, inline, ...props }: any) => {
                    if (inline) {
                      return <code className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-sm" {...props} />;
                    }
                    return <code className="block" {...props} />;
                  },
                }}
              >
                {markdownContent}
              </ReactMarkdown>
            </article>
          </div>
        </main>

        {/* Sidebar (desktop) */}
        <aside className="hidden lg:block w-80 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <Sidebar showNavigation={true} />
        </aside>
      </div>

      {/* Drawer móvil */}
      <MobileDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      >
        <Sidebar showNavigation={true} />
      </MobileDrawer>
    </div>
  );
}
