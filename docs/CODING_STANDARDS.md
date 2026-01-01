# Estándares de Código - Chatbot Legal Municipal

> **Fecha**: 2025-12-31  
> **Versión**: 1.0

---

## Reglas de Oro

1. **No hardcodear** - Usar variables de entorno y configuración
2. **No duplicar** - Extraer lógica común a funciones reutilizables
3. **Orden primero** - No hay prisa, priorizar calidad

---

## Reglas Específicas

### No Hardcodear

```typescript
// ❌ MAL
const API_KEY = 'sk-or-v1-083d62b6...';

// ✅ BIEN
const apiKey = process.env.OPENROUTER_API_KEY;
```

```typescript
// ❌ MAL
const municipalities = ['Avellaneda', 'Bahia Blanca', 'La Plata'];

// ✅ BIEN
const MUNICIPALITIES = [
  { id: '22', name: 'Avellaneda', slug: 'avellaneda' },
  { id: '1', name: 'Bahia Blanca', slug: 'bahia-blanca' },
  { id: '2', name: 'La Plata', slug: 'la-plata' },
] as const;

// Uso con tipado
const getMunicipality = (slug: typeof MUNICIPALITIES[number]['slug']) => 
  MUNICIPALITIES.find(m => m.slug === slug);
```

### No Duplicar Funciones

```typescript
// ❌ MAL - Lógica duplicada
async function getBoletin(id: string) {
  const response = await fetch(`${API_URL}/bulletins/${id}`);
  return response.json();
}

async function getNorma(id: string) {
  const response = await fetch(`${API_URL}/bulletins/${id}`);
  return response.json();
}

// ✅ BIEN - Función reutilizable
async function fetchFromAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

const getBoletin = (id: string) => fetchFromAPI<Boletin>(`/bulletins/${id}`);
const getNorma = (id: string) => fetchFromAPI<Norma>(`/norms/${id}`);
```

### DRY (Don't Repeat Yourself)

```typescript
// ❌ MAL - Código repetido
function validateChatMessage(msg: string) {
  if (msg.length === 0) throw new Error('Vacío');
  if (msg.length > 1000) throw new Error('Muy largo');
}

function validateSearchQuery(query: string) {
  if (query.length === 0) throw new Error('Vacío');
  if (query.length > 500) throw new Error('Muy largo');
}

// ✅ BIEN - Utilidades compartidas
const validators = {
  notEmpty: (field: string) => (value: string) => {
    if (!value.trim()) throw new Error(`${field} no puede estar vacío`);
  },
  maxLength: (field: string, max: number) => (value: string) => {
    if (value.length > max) throw new Error(`${field} máximo ${max} caracteres`);
  },
};

const validateChatMessage = (msg: string) => {
  validators.notEmpty('Mensaje')(msg);
  validators.maxLength('Mensaje', 1000)(msg);
};

const validateSearchQuery = (query: string) => {
  validators.notEmpty('Consulta')(query);
  validators.maxLength('Consulta', 500)(query);
};
```

---

## Estructura de Archivos

```
src/
├── lib/              # Utilidades y lógica compartida
│   ├── api.ts        # Funciones de API
│   ├── validators.ts # Validadores
│   ├── formatters.ts # Formateadores
│   └── constants.ts  # Constantes tipadas
├── components/       # Componentes UI
├── hooks/            # Custom hooks
├── types/            # Tipos compartidos
└── utils/            # Funciones helper
```

---

## Documentación de Código

### Cada función debe tener:

```typescript
/**
 * Descripción breve de lo que hace la función.
 * 
 * @param param1 - Descripción del parámetro 1
 * @param param2 - Descripción del parámetro 2
 * @returns Descripción de lo que retorna
 * 
 * @example
 * ```typescript
 * const result = miFuncion('hola', 123);
 * ```
 * 
 * @throws {ErrorType} Cuando ocurre este error
 */
function miFuncion(param1: string, param2: number): ResultType {
  // Implementación
}
```

---

## Principio DRY Aplicado

| Situación | Solución |
|-----------|----------|
| Lógica repetida | Extraer a función en `lib/` |
| Constantes repetidas | Centralizar en `constants.ts` |
| Tipos repetidos | Definir en `types/index.ts` |
| Configuración repetida | Usar archivos de config |
| Mensajes de error repetidos | Crear constants de errores |

---

## Checklist Antes de Commit

- [ ] No hay strings hardcodeados
- [ ] No hay lógica duplicada
- [ ] Funciones extraídas a lib/utils
- [ ] Tipos centralizados
- [ ] JSDoc completo
- [ ] Tests (cuando aplique)

---

*Estándares de Código v1.0*
*Generado: 2025-12-31*
