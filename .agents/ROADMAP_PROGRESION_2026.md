# 🚀 ROADMAP DE PROGRESIÓN - SIBOM Scraper Assistant

**Fecha de creación:** 2026-01-27
**Versión:** 1.0
**Estado:** Activo
**Responsable:** Martín Grinberg

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Estado Actual](#estado-actual)
3. [Problemas Identificados](#problemas-identificados)
4. [Plan Fase 1: Fix Chatbot](#plan-fase-1-fix-chatbot)
5. [Plan Fase 2: Frontend Unificado](#plan-fase-2-frontend-unificado)
6. [Plan Fase 3: Backend FastAPI](#plan-fase-3-backend-fastapi)
7. [Plan Fase 4: Sistema de Usuarios](#plan-fase-4-sistema-de-usuarios)
8. [Ideas Superadoras](#ideas-superadoras)
9. [Métricas de Éxito](#métricas-de-éxito)

---

## 🎯 VISIÓN GENERAL

**Objetivo a 12 meses:** Plataforma SaaS consolidada con dos productos principales:
1. **Chatbot Legal Municipal** - Búsqueda inteligente de normativas
2. **Análisis Satelital de Parcelas** - Monitoreo de humedales y vegetación

**Modelo de negocio:** Freemium con tier premium para análisis avanzado.

---

## 📊 ESTADO ACTUAL

### Componentes del Proyecto

| Componente | Estado | Calificación | Notas |
|------------|--------|--------------|-------|
| **Scraper (Python)** | ✅ Funcional | ⭐⭐⭐⭐ | Extrae datos de SIBOM correctamente |
| **Chatbot RAG** | ⚠️ Funcional con bugs | ⭐⭐⭐ | Necesita fixes y optimizaciones |
| **Sat-Analysis** | ✅ MVP funcional | ⭐⭐⭐⭐ | Código científico excelente |
| **Frontend Chatbot** | ⚠️ Solo pruebas | ⭐⭐ | LocalStorage, sin state management |
| **Frontend Sat** | ❌ No existe | - | Solo interfaz Gradio básica |
| **Infraestructura** | ⚠️ Parcial | ⭐⭐⭐ | Vercel + Railway, sin auth |

### Stack Tecnológico

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND                                │
├─────────────────────────────────────────────────────────────┤
│ Next.js 15 + React 19 + TypeScript                          │
│ Vercel AI SDK + OpenRouter                                  │
│ Tailwind CSS + Radix UI                                     │
│ ❌ Sin state management profesional                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (futuro)                        │
├─────────────────────────────────────────────────────────────┤
│ FastAPI + Python 3.13                                        │
│ PostgreSQL + Prisma                                         │
│ Redis para colas y cache                                    │
│ Qdrant para vector search                                   │
│ Cloudflare R2 para storage                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│ Scraper → GitHub Raw → RAG                                  │
│ Sentinel-2 → Microsoft Planetary Computer → Análisis        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐛 PROBLEMAS IDENTIFICADOS

### Chatbot - Críticos

1. **Uso extensivo de `any`** (81 ocurrencias en 21 archivos)
   - Compromete type safety
   - Errores en runtime potenciales

2. **Estado en LocalStorage**
   ```typescript
   localStorage.setItem('chat-filters', JSON.stringify(filters));
   localStorage.setItem('chat-history', JSON.stringify(messages));
   ```
   - Sin sincronización entre dispositivos
   - Sin persistencia real
   - Sin validación de esquema

3. **Componente ChatContainer monolítico**
   - 434 líneas en un solo archivo
   - Múltiples responsabilidades

4. **@ts-ignore para ReactMarkdown**
   ```typescript
   // @ts-ignore - CommonJS require para compatibilidad
   const ReactMarkdown = require('react-markdown').default;
   ```

5. **Sin error boundaries**
   - Fallos no controlados
   - Mala experiencia de usuario

### Frontend - Importantes

6. **Sin sistema de routing apropiado**
   - Solo una página principal
   - Sin deep linking

7. **Feedback visual insuficiente**
   - Estados de loading inconsistentes
   - Sin skeletons

8. **Falta de testing en componentes**
   - Tests solo en librerías utilitarias
   - Sin tests de integración UI

### Arquitectura

9. **API Route monolítica** (route.ts - 530 líneas)
10. **Sin separación de capas** (business logic en API routes)

---

## 📋 PLAN FASE 1: FIX CHATBOT (2-3 semanas)

### Objetivo
Chatbot estable, profesional y sin bugs críticos.

### Tareas

#### 1.1 Type Safety (3 días)
- [ ] Eliminar todos los `@ts-ignore`
- [ ] Reducir uso de `any` al mínimo (<10 ocurrencias)
- [ ] Crear tipos estrictos para:
  - `ChatMessage`
  - `ChatFilters`
  - `SearchResult`
  - `StreamData`

```typescript
// ANTES
const data: any = await response.json();

// DESPUÉS
interface ChatResponse {
  context: string;
  sources: Source[];
  usage?: UsageMetadata;
}
const data: ChatResponse = await response.json();
```

#### 1.2 State Management con Zustand (4 días)
- [ ] Instalar Zustand para estado global
- [ ] Crear stores:
  - `useChatStore` (mensajes, filters)
  - `useUIStore` (sidebar, modals)

```typescript
// stores/chat.ts
interface ChatStore {
  messages: ChatMessage[];
  filters: ChatFilters;
  addMessage: (message: ChatMessage) => void;
  setFilters: (filters: ChatFilters) => void;
  clearHistory: () => void;
}
```

- [ ] Migrar localStorage a Zustand persist
- [ ] Sincronización entre tabs

#### 1.3 Componentización (5 días)
- [ ] Dividir ChatContainer en:
  - `ChatMessages`
  - `ChatInput`
  - `ChatMessageList`
  - `StreamingResponse`
  - `SourcesPanel`

- [ ] Crear componentes atómicos:
  - `MessageBubble`
  - `SourceCard`
  - `FilterChip`
  - `LoadingSkeleton`

#### 1.4 Error Handling (2 días)
- [ ] Implementar ErrorBoundary
- [ ] Toast notifications para errores
- [ ] Retry automático con exponential backoff
- [ ] Graceful degradation

#### 1.5 Testing (3 días)
- [ ] Tests para componentes principales
- [ ] Tests de integración para API routes
- [ ] Tests E2E con Playwright

```typescript
// Ejemplo de test
describe('ChatContainer', () => {
  it('should display user message', () => {});
  it('should stream AI response', () => {});
  it('should handle API errors', () => {});
});
```

### Entregables Fase 1
- [ ] Chatbot sin errores de TypeScript
- [ ] Estado profesional con Zustand
- [ ] Componentes modulares
- [ ] Cobertura de tests >60%
- [ ] Documentación de componentes

---

## 📋 PLAN FASE 2: FRONTEND UNIFICADO (4-6 semanas)

### Objetivo
Frontend moderno y unificado para Chatbot + Sat-Analysis.

### Arquitectura Propuesta

```
src/
├── app/
│   ├── (auth)/           # Rutas protegidas
│   │   ├── chat/
│   │   ├── parcelas/
│   │   └── dashboard/
│   ├── (public)/         # Rutas públicas
│   │   ├── landing/
│   │   └── pricing/
│   └── api/
├── components/
│   ├── ui/               # shadcn/ui
│   ├── chat/
│   ├── parcels/
│   └── layout/
├── features/
│   ├── chat/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types.ts
│   └── parcels/
│       ├── hooks/
│       ├── services/
│       └── types.ts
├── lib/
│   ├── stores/           # Zustand
│   ├── api/              # Cliente API
│   └── utils/
└── styles/
```

### Tareas

#### 2.1 Sistema de UI (5 días)
- [ ] Instalar shadcn/ui
- [ ] Configurar tema personalizado
- [ ] Componentes base:
  - Button, Input, Select
  - Dialog, Sheet, Popover
  - Table, Badge, Alert

#### 2.2 Layout Unificado (4 días)
- [ ] Navbar responsive
- [ ] Sidebar navegable
- [ ] Footer legal
- [ ] Breadcrumbs

#### 2.3 Feature: Parcelas (7 días)
- [ ] Formulario de búsqueda por partida
- [ ] Mapa interactivo con Leaflet/Mapbox
- [ ] Timeline de imágenes satelitales
- [ ] Gráficos de evolución (Recharts)
- [ ] Export PDF

#### 2.4 Feature: Dashboard Usuario (5 días)
- [ ] Perfil de usuario
- [ ] Historial de consultas
- [ ] Estadísticas de uso
- [ ] Gestión de suscripción

#### 2.5 Optimizaciones (3 días)
- [ ] Server Components donde sea posible
- [ ] Streaming SSR
- [ ] Imagen optimizada (next/image)
- [ ] Code splitting por ruta

### Entregables Fase 2
- [ ] Frontend unificado funcional
- [ ] UI consistente con shadcn/ui
- [ ] Módulo de parcelas operativo
- [ ] Dashboard de usuario

---

## 📋 PLAN FASE 3: BACKEND FASTAPI (6-8 semanas)

### Objetivo
Backend robusto y escalable para soportar múltiples usuarios.

### Arquitectura

```
fastapi-backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── parcels.py
│   │   │   │   └── users.py
│   │   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── deps.py
│   ├── db/
│   │   ├── session.py
│   │   └── models.py
│   ├── services/
│   │   ├── rag_service.py
│   │   ├── satellite_service.py
│   │   └── user_service.py
│   └── main.py
├── tests/
│   ├── unit/
│   └── integration/
└── pyproject.toml
```

### Tareas

#### 3.1 Core Infrastructure (5 días)
- [ ] Setup FastAPI project
- [ ] SQLAlchemy + PostgreSQL
- [ ] Alembic migrations
- [ ] Pydantic v2 models

#### 3.2 Authentication (4 días)
- [ ] JWT tokens
- [ ] Password hashing (bcrypt)
- [ ] Refresh tokens
- [ ] OAuth2 providers (Google, GitHub)

#### 3.3 RAG Service (5 días)
- [ ] Migrar lógica desde chatbot
- [ ] Rate limiting por tier
- [ ] Caching con Redis
- [ ] Queue para queries pesadas

#### 3.4 Satellite Service (7 días)
- [ ] Integrar sat-analysis
- [ ] Procesamiento asíncrono (Celery)
- [ ] Almacenamiento de resultados
- [ ] Webhook de notificación

#### 3.5 API Documentation (2 días)
- [ ] OpenAPI/Swagger
- [ ] Postman collection
- [ ] Ejemplos de uso

### Entregables Fase 3
- [ ] Backend FastAPI funcional
- [ ] Authentication completo
- [ ] API documentada
- [ ] Tests integrales

---

## 📋 PLAN FASE 4: SISTEMA DE USUARIOS (4-6 semanas)

### Objetivo
Sistema completo de usuarios con tier free y premium.

### Tareas

#### 4.1 Database Schema (3 días)
```sql
-- users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  password_hash VARCHAR,
  subscription_tier VARCHAR DEFAULT 'free',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- usage tracking
CREATE TABLE usage_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action VARCHAR,
  tokens_used INT,
  timestamp TIMESTAMP
);

-- parcel analyses
CREATE TABLE parcel_analyses (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  partida VARCHAR,
  parameters JSONB,
  result_url VARCHAR,
  status VARCHAR,
  created_at TIMESTAMP
);
```

#### 4.2 Subscription Tiers (2 días)

| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| Precio | $0 | $9.99/mes | $29.99/mes |
| Queries/mes | 100 | 1,000 | Ilimitadas |
| Parcelas/mes | 1 | 10 | 100 |
| Años histórico | 1 | 5 | 10 |
| Imágenes/año | 2 | 4 | 12 |

#### 4.3 Stripe Integration (5 días)
- [ ] Checkout session
- [ ] Webhook handling
- [ ] Subscription management
- [ ] Portal de cliente

#### 4.4 Admin Dashboard (5 días)
- [ ] Lista de usuarios
- [ ] Métricas de uso
- [ ] Gestión de suscripciones
- [ ] Logs de actividad

### Entregables Fase 4
- [ ] Sistema de auth completo
- [ ] Pagos con Stripe
- [ ] Dashboard admin
- [ ] Tier enforcement

---

## 💡 IDEAS SUPERADORAS

### 1. **Features para el Chatbot**

#### AI-Powered
- [ ] **Resumen conversacional**: "¿Qué hablamos sobre tarifas en 2024?"
- [ ] **Comparación inteligente**: "Comparame las ordenanzas de tránsito entre La Plata y Bahía"
- [ ] **Citas legales**: Extraer artículos específicos mencionados
- [ ] **Contexto temporal**: "¿Cómo cambió la regulación de humedales desde 2020?"

#### UX/UI
- [ ] **Búsqueda predictiva**: Autocompletar mientras escribes
- [ ] **Sugerencias inteligentes**: "Otros buscaron..." basado en tu consulta
- [ ] **Vistas alternativas**: Tabla, Timeline, Mapa conceptual
- [ ] **Export multi-formato**: PDF, Word, Excel, Markdown

#### Colaboración
- [ ] **Compartir búsqueda**: URL con parámetros
- [ ] **Guardar colecciones**: "Mis normativas favoritas"
- [ ] **Notificaciones**: "Se publicó nueva normativa sobre X"

### 2. **Features para Sat-Analysis**

#### Análisis Avanzado
- [ ] **Series temporales**: Animación de evolución
- [ ] **Alertas automáticas**: "Detectado cambio significativo en parcela"
- [ ] **Comparación lado a lado**: Antes vs Después
- [ ] **Métricas personalizadas**: NDVI, NDWI, MNDWI, etc.

#### Integraciones
- [ ] **Datos climáticos**: Correlacionar con precipitación
- [ ] **Datos catastrales**: Integración ARBA completa
- [ ] **SIG desktop**: Export a QGIS/ArcGIS

#### Reportes
- [ ] **Reportes PDF automatizados**: Con branding del usuario
- [ ] **API para integradores**: Real estate, agronomía
- [ ] **Webhooks**: Notificar cuando termine análisis

### 3. **Features Plataforma**

#### Gamificación
- [ ] **Badges**: "Explorador de 50 municipios"
- [ ] **Streak**: Consultas consecutivas
- [ ] **Leaderboard**: Top contribuidores de feedback

#### Comunidad
- [ ] **Foro integrado**: Discutir normativas
- [ ] **Votos en normativas**: "¿Te resultó útil?"
- [ ] **Correcciones**: Reportar errores en OCR

#### API Pública
- [ ] **API key por usuario**
- [ ] **Webhooks para eventos**
- [ ] **SDK oficial**: Python + JavaScript
- [ ] **Playground interactivo**

### 4. **Infraestructura**

#### Performance
- [ ] **Edge Functions**: Cloudflare Workers para cache
- [ ] **CDN global**: Distribuir contenido estático
- [ ] **Image optimization**: WebP, AVIF, responsive
- [ ] **Prefetching inteligente**: Predecir próxima acción

#### Monitoreo
- [ ] **Sentry**: Error tracking
- [ ] **Vercel Analytics**: Web vitals
- [ ] **Posthog**: Product analytics
- [ ] **Grafana**: Dashboards de métricas

#### Cost Optimization
- [ ] **Model routing**: Queries simples → modelos baratos
- [ ] **Caching agresivo**: Redis + CDN
- [ ] **Compression**: Gzip todo lo posible
- [ ] **Serverless**: Solo pagar por uso real

### 5. **AI/ML Avanzado**

#### Fine-tuning
- [ ] **Modelo fine-tuneado**: Con normativas argentinas
- [ ] **Embeddings especializados**: Legal domain specific

#### Multimodal
- [ ] **Búsqueda por imagen**: "Buscá normativas similares a esta"
- [ ] **OCR en PDFs**: Cargar documentos propios

#### Voice
- [ ] **Dictado por voz**: "Buscá decretos de..."
- [ ] **Respuesta TTS**: Escuchar la norma

---

## 📈 MÉTRICAS ÉXITO

### Técnicas
- [ ] TypeScript: 0 errores, <5 `any`
- [ ] Tests: >70% cobertura
- [ ] Performance: Lighthouse >90
- [ ] Uptime: >99.5%

### Producto
- [ ] Tiempo de respuesta: <2s (percentil 95)
- [ ] Queries exitosas: >95%
- [ ] Retorno D1: >40%

### Negocio
- [ ] Usuarios activos: Creciendo 20%/mes
- [ ] Conversión Free→Paid: >3%
- [ ] Churn mensual: <5%

---

## 📝 NOTAS

### Prioridades Inmediatas (Esta semana)
1. Crear rama `feat/chatbot-fixes`
2. Configurar ESLint con reglas estrictas
3. Crear primer PR con fixes de TypeScript

### Decisión Pendiente
- [ ] ¿Mantener Vercel o migrar a Railway unificado?
- [ ] ¿Implementar auth propia o usar Auth0/Clerk?
- [ ] ¿SQLite dev vs PostgreSQL en staging?

---

**Última actualización:** 2026-01-27
**Próxima revisión:** 2026-02-03
