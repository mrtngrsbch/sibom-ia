'use client';

import { forwardRef } from 'react';

interface MangrulloProps {
  className?: string;
}

/**
 * Icono personalizado de Mangrullo
 * Representa la torre de vigilancia con refuerzos en X, ventana circular y mástil en el techo.
 * Réplica exacta del diseño de referencia.
 */
export const Mangrullo = forwardRef<SVGSVGElement, MangrulloProps>(
  ({ className }, ref) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1"
      className={className}
      ref={ref}
      viewBox="0 0 24 24"
    >
      {/* Línea base (suelo) */}
      <line x1="2" y1="22" x2="22" y2="22" />

      {/* Patas principales de la estructura */}
      <path d="M5 22 L8 10" />
      <path d="M19 22 L16 10" />

      {/* Plataforma */}
      <rect x="6" y="8" width="12" height="2" />

      {/* Cabina superior */}
      <rect x="8" y="3" width="8" height="5" />

      {/* Ventana circular */}
      <circle cx="12" cy="5.5" r="1.5" />

      {/* Techo a dos aguas */}
      <path d="M7 3 L12 1 L17 3" />

      {/* Mástil/Punta en el techo */}
      <line x1="12" y1="0" x2="12" y2="1" />

      {/* Estructura de refuerzo interna (X y travesaños) */}
      <line x1="6" y1="18" x2="18" y2="18" /> {/* Travesaño inferior */}
      <line x1="7" y1="14" x2="17" y2="14" /> {/* Travesaño medio */}
      <path d="M8 10 L18 18" /> {/* Diagonal 1 */}
      <path d="M16 10 L6 18" /> {/* Diagonal 2 */}
    </svg>
  )
);

Mangrullo.displayName = 'Mangrullo';