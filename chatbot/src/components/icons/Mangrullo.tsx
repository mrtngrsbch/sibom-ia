'use client';

import { forwardRef } from 'react';

interface MangrulloProps {
  className?: string;
}

/**
 * Icono personalizado de Mangrullo
 * Representa una torre de vigilancia típica de los humedales del Delta del Paraná
 */
export const Mangrullo = forwardRef<SVGSVGElement, MangrulloProps>(
  ({ className }, ref) => (
    <svg
      ref={ref}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {/* Base rectangular */}
      <rect x="6" y="14" width="12" height="6" rx="1" />
      
      {/* Soportes diagonales */}
      <line x1="6" y1="14" x2="8" y2="4" />
      <line x1="18" y1="14" x2="16" y2="4" />
      
      {/* Plataforma superior */}
      <rect x="5" y="4" width="14" height="2" rx="1" />
      
      {/* Techo triangular */}
      <path d="M7 4 L17 4" />
      
      {/* Ventana */}
      <rect x="10" y="16" width="4" height="3" rx="0.5" />
      
      {/* Escalera lateral */}
      <line x1="18" y1="20" x2="18" y2="22" />
      <line x1="18" y1="24" x2="18" y2="24" />
    </svg>
  )
);

Mangrullo.displayName = 'Mangrullo';
