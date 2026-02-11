/**
 * ChatErrorMessage.tsx
 *
 * Componente para mostrar errores del chat con opción de reintentar.
 */

'use client';

interface ChatErrorMessageProps {
  error: Error;
  onRetry: () => void;
}

export function ChatErrorMessage({ error, onRetry }: ChatErrorMessageProps) {
  return (
    <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400 flex flex-col gap-2">
      <p className="font-semibold">Hubo un error al procesar tu mensaje.</p>
      <p className="text-xs opacity-80">{error.message}</p>
      <button
        onClick={onRetry}
        className="mt-2 text-xs font-bold uppercase tracking-wider hover:underline text-left"
      >
        Reintentar consulta
      </button>
    </div>
  );
}
