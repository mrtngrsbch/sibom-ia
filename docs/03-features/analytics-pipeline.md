# SIBOM Analytics Pipeline & Dashboard

**Fecha de implementación:** 13 de Febrero de 2026
**Responsable:** Equipo de Ingeniería de Datos (AI Agents)
**Estado:** Producción

## 🏛️ Visión General

Este módulo transforma los datos crudos extraídos por el scraper (miles de archivos `*.json`) en un tablero de análisis de alto rendimiento para el usuario final.

La arquitectura sigue un patrón de **"Static Snapshot"** para desacoplar el procesamiento pesado (ETL) de la visualización (UI), garantizando tiempos de carga <100ms en el dashboard.

### Arquitectura de 3 Capas

1.  **Capa de Ingesta (ETL Python):** Escanea el sistema de archivos, resuelve relaciones lógicas y genera un snapshot canónico.
2.  **Capa de Validación (Middleware TS):** Carga el snapshot con validación estricta de tipos (Zod) en el servidor Next.js.
3.  **Capa de Presentación (React UI):** Visualiza los datos usando componentes interactivos (Server Components + Client Charts).

---

## ⚙️ 1. ETL Pipeline (Python)

El script `python-cli/scripts/build_analytics.py` es el motor de esta feature.

### Flujo de Procesamiento:
1.  **Deep Scan:** Recorre recursivamente `python-cli/boletines/` para encontrar todos los JSONs de boletines.
2.  **Bulletin ID Mapping:** Construye un mapa en memoria `{"Boletin_ID": "Municipio"}` analizando las URLs de origen.
3.  **Normativa Resolution:** Cruza las 390,000+ normativas indexadas (`normativas_index_minimal.json`) con el mapa de boletines para corregir atribuciones de municipios faltantes.
4.  **Agregación Estadística:** Calcula:
    *   Volumen total por tipo (Ordenanza, Decreto, etc.).
    *   Rango temporal (Primera y última fecha detectada).
    *   Distribución por años.

### Ejecución
Para actualizar los datos del dashboard (ej: después de un scraping masivo):

```bash
python python-cli/scripts/build_analytics.py
```

Esto regenera `data/indexes/analytics_snapshot.json`.

---

## 💾 2. Esquema de Datos (Snapshot)

El archivo intermedio `analytics_snapshot.json` es la fuente de verdad única para el frontend.

**Ubicación:** `python-cli/data/indexes/analytics_snapshot.json`

```typescript
// Estructura simplificada
{
  "generated_at": "2026-02-13T16:21:00",
  "global": {
    "total_documents": 34862,
    "total_municipalities": 32
  },
  "municipalities": [
    {
      "name": "Tandil",
      "stats": {
        "normativas": 5400,
        "last_date": "2024-01-15",
        ...
      },
      "breakdown": {
        "by_type": { "ordenanza": 3000, "decreto": 2400 },
        "by_year": [{ "year": 2023, "count": 1500 }]
      }
    }
  ]
}
```

---

## 🖥️ 3. Frontend Implementation (Next.js)

### Data Loader (`chatbot/src/lib/data/analytics-loader.ts`)
Implementa un patrón de carga robusto con **Zod**:
- Busca el snapshot en múltiples rutas (dev/prod).
- Valida que el JSON cumpla con el esquema esperado (evita crashes por datos corruptos).
- Implementa caching en memoria (TTL 1h) para no leer el disco en cada request.

### UI Components (`chatbot/src/components/analytics/*`)
- **DashboardClientView.tsx**: Componente cliente que maneja el estado de la UI (filtros, ordenamiento).
- **Gráficos (Recharts)**:
    - Histogramas de volumen.
    - Sparklines de actividad (roadmap).
- **Tablas**: Ordenables y filtrables en cliente para exploración rápida.

### Page (`/datos`)
Se refactorizó para ser un **Server Component**.
- **Antes**: Fetching via `useEffect` a `/api/municipios-stats` (lento, layout shift).
- **Ahora**: Inyección directa de datos en build/request time (Instantáneo, SEO-friendly).

---

## 🛠️ Mantenimiento

### ¿Cómo agregar una nueva métrica?
1.  Modificar **ETL**: `python-cli/scripts/build_analytics.py` para calcular la métrica.
2.  Actualizar **Schema**: `chatbot/src/lib/data/analytics-loader.ts` (Zod).
3.  Actualizar **UI**: `DashboardClientView.tsx` para mostrarla.

### Troubleshooting
- **Error "Analytics snapshot not found"**:
    - Causa: No se ha corrido el script ETL.
    - Solución: Ejecutar `python python-cli/scripts/build_analytics.py`.
- **Datos "0" en normativas**:
    - Causa: Fallo en el mapeo de IDs de boletines.
    - Solución: Verificar que los JSONs scraped tengan el campo `link` correctamente formado.
