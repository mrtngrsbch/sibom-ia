/**
 * @deprecated ELIMINADO en Sprint 4 — Duplicaba lógica de retriever.ts.
 * Este archivo puede borrarse con seguridad: rm chatbot/src/lib/rag/sqlite-retriever.ts
 * Razón: Reimplementaba filtros, stats y retrieval que ya existen en retriever.ts.
 * El flag USE_SQLITE nunca estaba activo en producción.
 * Si se necesita SQLite en el futuro, integrar directamente en retriever.ts como tercer backend.
 */
