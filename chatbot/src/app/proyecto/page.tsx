'use client';

import { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExternalLink } from '@/lib/icons';

/**
 * Página "Proyecto"
 * @description Muestra información sobre el proyecto, autor, motivación y objetivo
 */
export default function ProyectoPage() {
  const [markdownContent, setMarkdownContent] = useState('');
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    // Cargar el contenido del archivo Markdown
    fetch('/api/proyecto-content')
      .then(res => res.text())
      .then(content => setMarkdownContent(content))
      .catch(err => console.error('Error cargando contenido:', err));
  }, []);

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <Header onMenuClick={() => setIsDrawerOpen(true)} />

      {/* Contenedor principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Contenido principal */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto p-6 sm:p-8">
            {/* Contenido en Markdown */}
            <article className="prose prose-slate dark:prose-invert max-w-none
              prose-headings:font-bold
              prose-h1:text-4xl prose-h1:mb-6 prose-h1:text-slate-900 dark:prose-h1:text-white
              prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4 prose-h2:text-slate-800 dark:prose-h2:text-slate-200
              prose-p:text-slate-700 dark:prose-p:text-slate-300 prose-p:leading-relaxed
              prose-a:text-primary-600 dark:prose-a:text-primary-400 prose-a:no-underline hover:prose-a:underline
              prose-strong:text-slate-900 dark:prose-strong:text-white
              prose-ul:text-slate-700 dark:prose-ul:text-slate-300
              prose-li:text-slate-700 dark:prose-li:text-slate-300
              bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-8
            ">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ node, ...props }) => {
                    const isExternal = props.href?.startsWith('http');
                    return (
                      <a
                        {...props}
                        target={isExternal ? '_blank' : undefined}
                        rel={isExternal ? 'noopener noreferrer' : undefined}
                        className="inline-flex items-center gap-1 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                      >
                        {props.children}
                        {isExternal && <ExternalLink className="w-4 h-4" />}
                      </a>
                    );
                  },
                  hr: () => (
                    <hr className="my-8 border-slate-200 dark:border-slate-700" />
                  ),
                }}
              >
                {markdownContent}
              </ReactMarkdown>
            </article>
          </div>
        </main>

        {/* Sidebar - solo desktop */}
        <aside className="hidden lg:block w-80 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <Sidebar showNavigation={true} />
        </aside>
      </div>

      {/* Mobile Drawer */}
      <MobileDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      >
        <Sidebar showNavigation={true} />
      </MobileDrawer>
    </div>
  );
}
