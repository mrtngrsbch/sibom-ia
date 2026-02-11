/**
 * handlers/index.ts — Barrel export para handlers del chat API
 */

export { getStats, retrieveAndRerank } from './rag-handler';
export { tryHandleSQLComparison, buildSQLDirectResponse } from './sql-handler';
export { buildFAQPrompt, buildOffTopicPrompt, buildRAGPrompt } from './prompt-builder';
export { wrapStreamWithSources } from './stream-wrapper';
