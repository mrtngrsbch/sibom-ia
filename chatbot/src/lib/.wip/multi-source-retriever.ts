/**
 * Multi-Source RAG Retriever
 * Replaces the existing retriever with multi-source support
 */

import { multiSourceManager } from '../data-sources/multi-source-manager';
import { getConfigForEnvironment } from '../data-sources/config';
import { 
  UnifiedSearchFilters, 
  UnifiedSearchResult, 
  UnifiedDocument 
} from '../types-multi-source';

// Legacy compatibility types
import { SearchFilters, SearchResult, Source } from '../types';

/**
 * Initialize the multi-source RAG system
 */
export async function initializeMultiSourceRAG(): Promise<void> {
  try {
    console.log('[MultiSourceRAG] Initializing multi-source RAG system...');
    
    const configs = getConfigForEnvironment();
    await multiSourceManager.initialize(configs);
    
    console.log('[MultiSourceRAG] ✅ Multi-source RAG system initialized');
  } catch (error) {
    console.error('[MultiSourceRAG] ❌ Failed to initialize:', error);
    throw error;
  }
}

/**
 * Enhanced retrieve context function with multi-source support
 */
export async function retrieveContextMultiSource(
  query: string,
  options: SearchFilters = {}
): Promise<SearchResult> {
  try {
    // Convert legacy filters to unified format
    const unifiedFilters: UnifiedSearchFilters = {
      query,
      municipality: options.municipality || undefined,
      documentType: options.type || undefined,
      publishedAfter: options.dateFrom || undefined,
      publishedBefore: options.dateTo || undefined,
      limit: options.limit || 10,
      
      // Default to legal category for backward compatibility
      category: 'legal',
      
      // Sort by relevance by default
      sortBy: 'relevance',
      sortOrder: 'desc'
    };

    // Search across all sources
    const result = await multiSourceManager.search(unifiedFilters);
    
    // Convert back to legacy format for compatibility
    return convertToLegacyResult(result);
    
  } catch (error) {
    console.error('[MultiSourceRAG] Search error:', error);
    
    // Return empty result on error
    return {
      context: 'Error al buscar documentos. Intenta nuevamente.',
      sources: []
    };
  }
}

/**
 * Get document by ID from any source
 */
export async function getDocumentById(id: string): Promise<UnifiedDocument | null> {
  try {
    return await multiSourceManager.getDocument(id);
  } catch (error) {
    console.error('[MultiSourceRAG] Error getting document:', error);
    return null;
  }
}

/**
 * Get database statistics from all sources
 */
export async function getDatabaseStatsMultiSource() {
  try {
    const healthReports = await multiSourceManager.getHealthStatus();
    
    const totalDocuments = healthReports.reduce((sum, report) => 
      sum + (report.stats?.totalDocuments || 0), 0
    );
    
    const municipalities = new Set<string>();
    const sourceTypes = new Set<string>();
    
    healthReports.forEach(report => {
      sourceTypes.add(report.sourceType);
      // TODO: Extract municipalities from each source
    });

    return {
      totalDocuments,
      municipalities: municipalities.size,
      municipalityList: Array.from(municipalities),
      sources: healthReports.length,
      sourceTypes: Array.from(sourceTypes),
      lastUpdated: new Date().toISOString(),
      healthReports
    };
    
  } catch (error) {
    console.error('[MultiSourceRAG] Error getting stats:', error);
    return {
      totalDocuments: 0,
      municipalities: 0,
      municipalityList: [],
      sources: 0,
      sourceTypes: [],
      lastUpdated: null,
      healthReports: []
    };
  }
}

/**
 * Refresh all data sources
 */
export async function refreshAllSources(): Promise<void> {
  try {
    await multiSourceManager.refreshAll();
  } catch (error) {
    console.error('[MultiSourceRAG] Error refreshing sources:', error);
    throw error;
  }
}

/**
 * Add a new document to manual upload source
 */
export async function uploadDocument(
  file: File,
  metadata: Partial<UnifiedDocument>,
  userId: string = 'anonymous'
): Promise<UnifiedDocument> {
  try {
    const manualUploadSource = multiSourceManager.getSource('manual_upload_primary');
    
    if (!manualUploadSource) {
      throw new Error('Manual upload source not available');
    }

    // Cast to ManualUploadDataSource to access upload method
    const uploadSource = manualUploadSource as any;
    
    if (!uploadSource.uploadDocument) {
      throw new Error('Upload functionality not available');
    }

    return await uploadSource.uploadDocument(file, metadata, userId);
    
  } catch (error) {
    console.error('[MultiSourceRAG] Error uploading document:', error);
    throw error;
  }
}

/**
 * Delete a document from manual upload source
 */
export async function deleteDocument(id: string): Promise<boolean> {
  try {
    const manualUploadSource = multiSourceManager.getSource('manual_upload_primary');
    
    if (!manualUploadSource) {
      throw new Error('Manual upload source not available');
    }

    const uploadSource = manualUploadSource as any;
    
    if (!uploadSource.deleteDocument) {
      throw new Error('Delete functionality not available');
    }

    return await uploadSource.deleteDocument(id);
    
  } catch (error) {
    console.error('[MultiSourceRAG] Error deleting document:', error);
    return false;
  }
}

// ============================================================================
// LEGACY COMPATIBILITY
// ============================================================================

/**
 * Legacy retrieve context function (backward compatibility)
 */
export async function retrieveContext(
  query: string,
  options: SearchFilters = {}
): Promise<SearchResult> {
  return retrieveContextMultiSource(query, options);
}

/**
 * Legacy get database stats function (backward compatibility)
 */
export async function getDatabaseStats() {
  const stats = await getDatabaseStatsMultiSource();
  
  // Return in legacy format
  return {
    totalDocuments: stats.totalDocuments,
    municipalities: stats.municipalities,
    municipalityList: stats.municipalityList,
    lastUpdated: stats.lastUpdated
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Convert unified result to legacy format
 */
function convertToLegacyResult(result: UnifiedSearchResult): SearchResult {
  // Build context from documents
  const context = result.documents.length > 0 
    ? buildContextFromDocuments(result.documents)
    : 'No se encontraron documentos relevantes.';

  // Convert documents to legacy sources
  const sources: Source[] = result.documents.map(doc => ({
    title: doc.title,
    url: doc.url || '#',
    municipality: doc.municipality || 'N/A',
    type: doc.documentType || doc.category,
    status: doc.status || undefined,
    documentTypes: doc.documentType ? [doc.documentType as any] : undefined
  }));

  return {
    context,
    sources
  };
}

/**
 * Build context text from documents
 */
function buildContextFromDocuments(documents: UnifiedDocument[]): string {
  const contextParts: string[] = [];

  documents.forEach((doc, index) => {
    const docInfo = [
      `**${doc.title}**`,
      doc.municipality ? `Municipio: ${doc.municipality}` : null,
      doc.officialNumber ? `Número: ${doc.officialNumber}` : null,
      doc.publishedDate ? `Fecha: ${doc.publishedDate}` : null,
      doc.status ? `Estado: ${doc.status}` : null
    ].filter(Boolean).join(' | ');

    contextParts.push(`${index + 1}. ${docInfo}`);
    
    if (doc.summary) {
      contextParts.push(`   ${doc.summary}`);
    } else if (doc.content) {
      // Use first 200 characters as summary
      const summary = doc.content.slice(0, 200).trim();
      contextParts.push(`   ${summary}${doc.content.length > 200 ? '...' : ''}`);
    }
    
    contextParts.push(''); // Empty line between documents
  });

  return contextParts.join('\n');
}

/**
 * Check if multi-source RAG is initialized
 */
export function isMultiSourceInitialized(): boolean {
  return multiSourceManager['isInitialized'] || false;
}

/**
 * Get available source types
 */
export function getAvailableSourceTypes(): string[] {
  return multiSourceManager.getSourceConfigs().map(config => config.type);
}

/**
 * Get source health status
 */
export async function getSourcesHealth() {
  return multiSourceManager.getHealthStatus();
}