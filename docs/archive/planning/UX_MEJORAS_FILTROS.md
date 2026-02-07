# Mejoras UX - Rediseño de Filtros

## Cambios Implementados

### ✅ 1. Padding del Chat aumentado a 130px

**Antes**: `p-4 sm:p-6`
**Después**: `p-4 sm:p-6 pb-[130px]`

Esto deja espacio en la parte inferior para que el FilterBar no tape los mensajes.

### ✅ 2. FilterBar Movido Abajo

**Ubicación anterior**: Arriba del área de mensajes (header)
**Ubicación nueva**: Abajo del chat, como barra fija en la parte inferior

**Ventajas**:
- No ocupa espacio del chat principal
- Siempre visible (fixed)
- Más accesible desde el input de texto
- Más espacio para mensajes

### ✅ 3. Rediseño con Badges de shadcn

**Estilo anterior**: Barra horizontal con botones grandes y dropdowns
**Estilo nuevo**: Badges compactos con dropdowns popup

## Características del Nuevo Diseño

### Badges Interactivos

Cada filtro es un badge que puede estar en 2 estados:

#### **Estado Inactivo** (outline)
```tsx
<Badge variant="outline">
  <MapPin /> Municipio
  <ChevronDown />
</Badge>
```
- Borde gris
- Icono + texto + chevron
- Click abre dropdown

#### **Estado Activo** (default)
```tsx
<Badge variant="default">
  <MapPin /> Carlos Tejedor
  <X />
</Badge>
```
- Fondo oscuro
- Icono + valor seleccionado + X para limpiar
- Click abre dropdown
- X limpia el filtro

### 3 Filtros Disponibles

1. **Municipio** 📍
   - Icono: `MapPin`
   - Dropdown: Lista scrolleable de 34 municipios
   - Width: 224px (w-56)
   - Max height: 240px (max-h-60)

2. **Tipo** 📄
   - Icono: `FileText`
   - Opciones: Todos, Ordenanzas, Decretos, Boletines
   - Width: 160px (w-40)

3. **Fecha** 📅
   - Icono: `Calendar`
   - Dropdown: 2 inputs de fecha (Desde/Hasta)
   - Width: 288px (w-72)
   - Muestra rango seleccionado: `2025-01-01 - 2025-12-31`

### Botón "Limpiar filtros"

Aparece solo cuando hay al menos un filtro activo:
```tsx
{(filters.municipality || filters.ordinanceType !== 'all' || ...) && (
  <button>Limpiar filtros</button>
)}
```

## Estructura del FilterBar

```tsx
<div className="fixed bottom-0 left-0 right-0 bg-white border-t p-3 z-10">
  <div className="max-w-3xl mx-auto">
    <div className="flex items-center gap-2 flex-wrap">
      <span>Filtros:</span>

      {/* Badge Municipio */}
      <Badge variant={...} onClick={...}>
        <MapPin /> {municipality || 'Municipio'}
        <X | ChevronDown />
      </Badge>

      {/* Badge Tipo */}
      <Badge variant={...} onClick={...}>
        <FileText /> {tipo}
        <X | ChevronDown />
      </Badge>

      {/* Badge Fecha */}
      <Badge variant={...} onClick={...}>
        <Calendar /> {rango || 'Fecha'}
        <X | ChevronDown />
      </Badge>

      {/* Limpiar todo */}
      <button>Limpiar filtros</button>
    </div>
  </div>
</div>
```

## Dropdowns

Todos los dropdowns se abren **hacia arriba** (bottom-full mb-2):

```tsx
<div className="absolute bottom-full mb-2 left-0 bg-white border rounded-lg shadow-lg">
  {/* Contenido */}
</div>
```

**Por qué hacia arriba?**
- El FilterBar está en la parte inferior
- Si se abrieran hacia abajo quedarían fuera de la pantalla
- `bottom-full` los posiciona justo arriba del badge
- `mb-2` agrega 8px de margen

## Clases CSS Utilizadas

### Badge Base
```css
inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold
```

### Badge Interactivo (custom)
```css
cursor-pointer hover:opacity-80 transition-opacity pl-2 pr-1 py-1 gap-1
```

### Dropdown
```css
absolute bottom-full mb-2 left-0 bg-white dark:bg-slate-800
border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50
```

### Opciones del Dropdown
```css
px-3 py-2 text-sm rounded hover:bg-slate-100 dark:hover:bg-slate-700
```

## Comportamiento

### Click en Badge
- Abre/cierra el dropdown correspondiente
- Cierra otros dropdowns abiertos (via state)

### Click en X
- `e.stopPropagation()` previene que se abra el dropdown
- Limpia el filtro específico
- No cierra el dropdown si estaba abierto

### Click fuera
- `useEffect` + `mousedown` event listener
- Detecta clicks fuera de cada ref
- Cierra dropdowns automáticamente

### Selección de valor
- Actualiza el filtro via `onChange`
- Cierra el dropdown automáticamente
- Badge cambia de `outline` a `default`

## Comparación con Diseño Anterior

### Antes
```
┌─────────────────────────────────────────────────────┐
│ [Filtros horizontales grandes]                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Área de mensajes                                   │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Input de chat                                       │
└─────────────────────────────────────────────────────┘
```

### Después
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Área de mensajes (más espacio!)                    │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Input de chat                                       │
├─────────────────────────────────────────────────────┤
│ Filtros: [📍 Municipio] [📄 Tipo] [📅 Fecha]      │
└─────────────────────────────────────────────────────┘
```

## Ventajas del Nuevo Diseño

✅ **Más espacio para mensajes** - El chat ocupa toda la altura
✅ **Filtros siempre visibles** - Fixed bottom, no se pierden al scrollear
✅ **Compacto** - Badges ocupan menos espacio que botones grandes
✅ **Visual claro** - Se ve de un vistazo qué filtros están activos
✅ **Fácil de limpiar** - Cada badge tiene su X, más botón "Limpiar todo"
✅ **Responsive** - flex-wrap permite que se ajusten en móviles
✅ **Consistente** - Usa componentes de shadcn (Badge)

## Mobile Responsiveness

En pantallas pequeñas:
- `flex-wrap` permite que los badges pasen a múltiples líneas
- Dropdowns se adaptan al ancho disponible
- Fixed bottom sigue funcionando
- Padding aumentado (130px) asegura que no tapen contenido

## Dark Mode

Todos los componentes tienen soporte para dark mode:
- `dark:bg-slate-900` en el FilterBar
- `dark:bg-slate-800` en dropdowns
- `dark:border-slate-700` en bordes
- `dark:hover:bg-slate-700` en opciones

## Z-Index

- FilterBar: `z-10` (fijo en el bottom)
- Dropdowns: `z-50` (sobre el FilterBar)
- Asegura que los dropdowns nunca queden detrás de otros elementos
