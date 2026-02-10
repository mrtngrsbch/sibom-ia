# Iconos Personalizados

Este directorio contiene iconos personalizados que siguen el estilo de Lucide.dev.

## Mangrullo

El icono de Mangrullo representa una torre de vigilancia típica de los humedales del Delta del Paraná.

### Uso

```tsx
import { Mangrullo } from '@/lib/icons';

// Uso básico
<Mangrullo className="w-6 h-6" />

// Con color personalizado
<Mangrullo className="w-8 h-8 text-primary-600" />

// En un botón
<Button>
  <Mangrullo className="w-4 h-4 mr-2" />
  Mangrullo
</Button>
```

### Características del diseño

- **Estilo Lucide**: Minimalista, stroke 2px, round caps/joins
- **Elementos**:
  - Base rectangular
  - Soportes diagonales
  - Plataforma superior
  - Techo triangular
  - Ventana
  - Escalera lateral

### Significado cultural

Un mangrullo es una estructura de madera elevada que se usa tradicionalmente en los humedales del Delta del Paraná para:
- Vigilar el ganado
- Observar el terreno
- Protegerse de inundaciones
- Tener una vista panorámica del entorno

## Agregar nuevos iconos

Para agregar un nuevo icono personalizado:

1. Crear un archivo `.tsx` en este directorio
2. Seguir el estilo de Lucide (stroke 2px, round caps/joins)
3. Exportar el icono desde `@/lib/icons`

Ejemplo:

```tsx
// chatbot/src/components/icons/MiIcono.tsx
import { forwardRef } from 'react';

export const MiIcono = forwardRef<SVGSVGElement, React.SVGProps<SVGSVGElement>>(
  ({ className, ...props }, ref) => (
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
      {...props}
    >
      {/* Tu icono aquí */}
    </svg>
  )
);

MiIcono.displayName = 'MiIcono';
```

Luego exportarlo desde `@/lib/icons`:

```typescript
// chatbot/src/lib/icons.ts
export { MiIcono } from '@/components/icons/MiIcono';
```
