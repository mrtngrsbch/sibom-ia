import { ChatContainer } from '@/components/chat/ChatContainer';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';

/**
 * Página principal del Chatbot Legal Municipal
 * @description Interface de chat con panel lateral de navegación
 */
export default function HomePage() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Panel lateral */}
      <aside className="hidden lg:flex w-72 flex-col border-r border-slate-200 dark:border-slate-800">
        <Sidebar />
      </aside>

      {/* Contenido principal */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
          <Header />
        </header>

        {/* Área del chat */}
        <div className="flex-1 overflow-hidden">
          <ChatContainer />
        </div>
      </main>
    </div>
  );
}
