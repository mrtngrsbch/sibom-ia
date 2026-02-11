# Plan Maestro de Refactorización: Arquitectura RAG Híbrida Serverless (Free Tier)

**Versión:** 2.0.0
**Fecha:** Enero 2026
**Autor:** AI Assistant (Role: Senior Software Engineer)
**Estado:** Pendiente de Ejecución

## 1. Resumen Ejecutivo

El sistema actual utiliza una arquitectura de "Búsqueda en Memoria" donde el backend descarga y procesa archivos JSON masivos (1.7 GB proyectados) en tiempo de ejecución. Esto es insostenible para el escalado y el rendimiento.

Este plan detalla la migración a una **Arquitectura RAG Híbrida Serverless** diseñada específicamente para operar dentro de los límites gratuitos (Free Tier) de proveedores modernos, soportando +12,000 documentos con latencia mínima.

### La "Tríada Serverless"
1.  **Cerebro (Supabase Postgres):** Almacena **vectores (embeddings)** y metadatos ligeros. Utiliza `pgvector` para búsqueda semántica.
2.  **Memoria (Cloudflare R2):** Almacena el **contenido completo (JSON/Texto)**. Actúa como Object Storage compatible con S3.
3.  **Procesamiento (OpenAI + Vercel):** Generación de embeddings y orquestación de la lógica.

---

## 2. Prerrequisitos y Configuración

### 2.1. Servicios Requeridos
1.  **Supabase:** Proyecto nuevo con `pgvector` habilitado.
2.  **Cloudflare R2:** Bucket creado (ej: `sibom-data`).
3.  **OpenAI:** API Key (Modelo: `text-embedding-3-small`).

### 2.2. Variables de Entorno (`.env`)
```env
NEXT_PUBLIC_SUPABASE_URL="https://xxx.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="ey..."
SUPABASE_SERVICE_ROLE_KEY="ey..."
R2_ACCOUNT_ID="xxx"
R2_ACCESS_KEY_ID="xxx"
R2_SECRET_ACCESS_KEY="xxx"
R2_BUCKET_NAME="sibom-data"
OPENAI_API_KEY="sk-..."
```

---

## 3. Fase 1: Infraestructura de Datos (SQL Schema)

Ejecutar en el Editor SQL de Supabase:

```sql
create extension if not exists vector;

create table documents (
  id bigserial primary key,
  r2_key text not null unique,
  municipality text not null,
  doc_type text not null,
  doc_number text,
  title text,
  date date,
  url text,
  token_count int,
  created_at timestamptz default now()
);

create table document_chunks (
  id bigserial primary key,
  document_id bigint references documents(id) on delete cascade,
  chunk_index int not null,
  content_preview text,
  embedding vector(1536)
);

create index on document_chunks using hnsw (embedding vector_cosine_ops);
create index idx_documents_municipality on documents(municipality);
create index idx_documents_date on documents(date);
```

---

## 4. Fase 2: Pipeline de Migración (Python)

**Script:** `python-cli/migrate_to_cloud.py`

1.  **Carga:** Lee JSON local.
2.  **Upload:** Sube el JSON comprimido a Cloudflare R2.
3.  **Embed:** Divide texto en chunks y genera vectores con OpenAI.
4.  **Index:** Guarda metadata y vectores en Supabase.

---

## 5. Fase 3: Backend Refactor (Next.js)

Actualizar `retriever.ts` para:
1.  Generar embedding de la consulta del usuario.
2.  Llamar a Supabase para obtener los 5 documentos más relevantes (IDs y R2 Keys).
3.  Descargar el contenido completo desde Cloudflare R2 solo para esos 5 documentos.
4.  Inyectar el contexto en el Prompt de Claude.

---

## 6. Fase 4: Frontend y UX

1.  **useChatController:** Extraer lógica de estado de `ChatContainer`.
2.  **Skeletons:** Feedback visual mientras se consultan vectores y R2.
3.  **Citations:** Mostrar fuentes basadas en la metadata de la DB.
