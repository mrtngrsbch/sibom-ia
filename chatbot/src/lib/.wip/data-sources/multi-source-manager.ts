/**
 * Multi-Source Manager
 * Orchestrates multiple data sources for unified search
 */

import { BaseDataSource, DataSourceFactory } from './base-source';
import { SIBOMDataSource } from './sibom-source';
import { ManualUploadDataSource } from './manual-upload-source';
import { 
  UnifiedDocument, 
  UnifiedSearchFilters, 
  UnifiedSearchResult,
  DataSourceConfig,
  DataSourceType 
} from '../types-multi-source';

/**
 * Multi-source manager for unified RAG
 */
export class MultiSourceManager {
  private sources = new Map<string, BaseDataSource>();
  private isInitialized = false;

  constructor() {
    // Register built-in data sources
    DataSourceFactory.register('sibom_scraping', SIBOMDataSource);
    DataSourceFactory.register('manual_upload', ManualUploadDataSource);
  }

  /**
   * Initialize with configuration
   */
  async initialize(configs: DataSourceConfig[]): Promise<void> {
    console.log('[MultiSource] Initializing multi-source manager...');
    
    try {
      // Create and initialize all sources
      for (const config of configs) {
        if (!config.enabled) {
          console.log(`[MultiSource] Skipping disabled source: ${config.name}`);
          continue;
        }

        console.log(`[MultiSource] Initializing source: ${config.name} (${config.type})`);
        
        const source = DataSourceFactory.create(config);
        await source.initialize();
        
        this.sources.set(config.id, source);
        console.log(`[MultiSource] ✅ Source initialized: ${config.name}`);
      }

      this.isInitialized = true;
      console.log(`[MultiSource] ✅ Manager initialized with ${this.sources.size} sources`);
      
    } catch (error) {
      console.error('[MultiSource] ❌ Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Unified search across all sources
   */
  async search(filters: UnifiedSearchFilters): Promise<UnifiedSearchResult> {
    if (!this.isInitialized) {
      throw new Error('Multi-source manager not initialized');
    }

    const startTime = Date.now();
    
    try {
      // Determine which sources to query
      const sourcesToQuery = this.selectSources(filters);
      
      if (sourcesToQuery.length === 0) {
        return this.emptyResult(filters.query || '', startTime);
      }

      // Query sources in parallel
      const searchPromises = sourcesToQuery.map(async source => {
        try {
          const result = await source.search(filters);
          return {
            source: source.getConfig(),
            result,
            error: null
          };
        } catch (error) {
          console.error(`[MultiSource] Search failed for ${source.getConfig().name}:`, error);
          return {
            source: source.getConfig(),
            result: null,
            error: error.message
          };
        }
      });

      const searchResults = await Promise.all(searchPromises);
      
      // Merge and rank results
      const mergedResult = this.mergeResults(searchResults, filters);
      
      const executionTime = Date.now() - startTime;
      mergedResult.searchMetadata.executionTimeMs = executionTime;
      
      console.log(`[MultiSource] Search completed in ${executionTime}ms: ${mergedResult.documents.length} results`);
      
      return mergedResult;

    } catch (error) {
      console.error('[MultiSource] Search error:', error);
      throw error;
    }
  }

  /**
   * Get document by ID from any source
   */
  async getDocument(id: string): Promise<UnifiedDocument | null> {
    // Try each source until we find the document
    for (const source of this.sources.values()) {
      try {
        const document = await source.getDocument(id);
        if (document) {
          return document;
        }
      } catch (error) {
        console.warn(`[MultiSource] Failed to get document ${id} from ${source.getConfig().name}:`, error);
      }
    }
    
    return null;
  }

  /**
   * Get all documents from all sources (paginated)
   */
  async getAllDocuments(offset = 0, limit = 100): Promise<UnifiedDocument[]> {
    const allDocuments: UnifiedDocument[] = [];
    
    // Get documents from all sources
    for (const source of this.sources.values()) {
      try {
        const documents = await source.getAllDocuments(0, limit); // Get up to limit from each
        allDocuments.push(...documents);
      } catch (error) {
        console.warn(`[MultiSource] Failed to get documents from ${source.getConfig().name}:`, error);
      }
    }
    
    // Sort by priority and date
    allDocuments.sort((a, b) => {
      // First by source priority
      const sourceA = this.getSourceByType(a.sourceType);
      const sourceB = this.getSourceByType(b.sourceType);
      
      if (sourceA && sourceB) {
        const priorityDiff = sourceB.getPriority() - sourceA.getPriority();
        if (priorityDiff !== 0) return priorityDiff;
      }
      
      // Then by date (newest first)
      const dateA = a.publishedDate || a.createdAt;
      const dateB = b.publishedDate || b.createdAt;
      return dateB.localeCompare(dateA);
    });
    
    // Apply pagination
    return allDocuments.slice(offset, offset + limit);
  }

  /**
   * Refresh all sources
   */
  async refreshAll(): Promise<void> {
    console.log('[MultiSource] Refreshing all sources...');
    
    const refreshPromises = Array.from(this.sources.values()).map(async source => {
      try {
        await source.refresh();
        console.log(`[MultiSource] ✅ Refreshed: ${source.getConfig().name}`);
      } catch (error) {
        console.error(`[MultiSource] ❌ Failed to refresh ${source.getConfig().name}:`, error);
      }
    });

    await Promise.all(refreshPromises);
    console.log('[MultiSource] ✅ All sources refreshed');
  }

  /**
   * Get health status of all sources
   */
  async getHealthStatus(): Promise<SourceHealthReport[]> {
    const healthPromises = Array.from(this.sources.values()).map(async source => {
      try {
        const health = await source.healthCheck();
        const stats = await source.getStats();
        
        return {
          sourceId: source.getConfig().id,
          sourceName: source.getConfig().name,
          sourceType: source.getType(),
          health,
          stats
        };
      } catch (error) {
        return {
          sourceId: source.getConfig().id,
          sourceName: source.getConfig().name,
          sourceType: source.getType(),
          health: {
            status: 'unhealthy' as const,
            message: `Health check failed: ${error.message}`,
            lastChecked: new Date().toISOString()
          },
          stats: null
        };
      }
    });

    return Promise.all(healthPromises);
  }

  /**
   * Add a new data source
   */
  async addSource(config: DataSourceConfig): Promise<void> {
    if (this.sources.has(config.id)) {
      throw new Error(`Source with ID ${config.id} already exists`);
    }

    const source = DataSourceFactory.create(config);
    await source.initialize();
    
    this.sources.set(config.id, source);
    console.log(`[MultiSource] ✅ Added source: ${config.name}`);
  }

  /**
   * Remove a data source
   */
  async removeSource(sourceId: string): Promise<boolean> {
    const source = this.sources.get(sourceId);
    if (!source) {
      return false;
    }

    this.sources.delete(sourceId);
    console.log(`[MultiSource] ✅ Removed source: ${source.getConfig().name}`);
    return true;
  }

  /**
   * Get source by ID
   */
  getSource(sourceId: string): BaseDataSource | undefined {
    return this.sources.get(sourceId);
  }

  /**
   * Get all source configurations
   */
  getSourceConfigs(): DataSourceConfig[] {
    return Array.from(this.sources.values()).map(source => source.getConfig());
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  /**
   * Select which sources to query based on filters
   */
  private selectSources(filters: UnifiedSearchFilters): BaseDataSource[] {
    const availableSources = Array.from(this.sources.values()).filter(source => 
      source.isEnabled() && source.isReady()
    );

    // If specific source types requested, filter by those
    if (filters.sourceTypes && filters.sourceTypes.length > 0) {
      return availableSources.filter(source => 
        filters.sourceTypes!.includes(source.getType())
      );
    }

    // If specific source IDs requested, filter by those
    if (filters.sourceIds && filters.sourceIds.length > 0) {
      return availableSources.filter(source => 
        filters.sourceIds!.includes(source.getConfig().id)
      );
    }

    // Return all available sources
    return availableSources;
  }

  /**
   * Merge results from multiple sources
   */
  private mergeResults(
    searchResults: SourceSearchResult[], 
    filters: UnifiedSearchFilters
  ): UnifiedSearchResult {
    const allDocuments: UnifiedDocument[] = [];
    const allFacets = {
      categories: new Map<string, number>(),
      sourceTypes: new Map<string, number>(),
      municipalities: new Map<string, number>(),
      documentTypes: new Map<string, number>(),
      status: new Map<string, number>(),
      languages: new Map<string, number>()
    };
    
    let totalCount = 0;
    const sourcesQueried: DataSourceType[] = [];

    // Collect all documents and facets
    for (const { source, result, error } of searchResults) {
      sourcesQueried.push(source.type);
      
      if (!result || error) {
        continue;
      }

      // Add documents with source priority weighting
      const documentsWithPriority = result.documents.map(doc => ({
        ...doc,
        _priority: source.priority,
        _sourceScore: 1.0 // Could be BM25 score or similar
      }));

      allDocuments.push(...documentsWithPriority);
      totalCount += result.totalCount;

      // Merge facets
      this.mergeFacets(allFacets, result.facets);
    }

    // Sort documents by relevance and priority
    allDocuments.sort((a, b) => {
      // First by source priority
      const priorityDiff = (b as any)._priority - (a as any)._priority;
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then by date (newest first)
      const dateA = a.publishedDate || a.createdAt;
      const dateB = b.publishedDate || b.createdAt;
      return dateB.localeCompare(dateA);
    });

    // Apply final limit
    const limit = filters.limit || 10;
    const finalDocuments = allDocuments.slice(0, limit);

    // Convert facet maps to arrays
    const facets = {
      categories: Array.from(allFacets.categories.entries()).map(([value, count]) => ({ value, count })),
      sourceTypes: Array.from(allFacets.sourceTypes.entries()).map(([value, count]) => ({ value, count })),
      municipalities: Array.from(allFacets.municipalities.entries()).map(([value, count]) => ({ value, count })),
      documentTypes: Array.from(allFacets.documentTypes.entries()).map(([value, count]) => ({ value, count })),
      status: Array.from(allFacets.status.entries()).map(([value, count]) => ({ value, count })),
      languages: Array.from(allFacets.languages.entries()).map(([value, count]) => ({ value, count }))
    };

    return {
      documents: finalDocuments,
      totalCount,
      facets,
      searchMetadata: {
        query: filters.query || '',
        executionTimeMs: 0, // Will be set by caller
        totalSources: this.sources.size,
        sourcesQueried,
        cacheHit: false
      }
    };
  }

  /**
   * Merge facets from multiple sources
   */
  private mergeFacets(target: any, source: any): void {
    for (const [key, facetArray] of Object.entries(source)) {
      const targetMap = target[key];
      if (targetMap && Array.isArray(facetArray)) {
        for (const { value, count } of facetArray as any[]) {
          targetMap.set(value, (targetMap.get(value) || 0) + count);
        }
      }
    }
  }

  /**
   * Get source by type
   */
  private getSourceByType(type: DataSourceType): BaseDataSource | undefined {
    return Array.from(this.sources.values()).find(source => source.getType() === type);
  }

  /**
   * Create empty result
   */
  private emptyResult(query: string, startTime: number): UnifiedSearchResult {
    return {
      documents: [],
      totalCount: 0,
      facets: {
        categories: [],
        sourceTypes: [],
        municipalities: [],
        documentTypes: [],
        status: [],
        languages: []
      },
      searchMetadata: {
        query,
        executionTimeMs: Date.now() - startTime,
        totalSources: this.sources.size,
        sourcesQueried: [],
        cacheHit: false
      }
    };
  }
}

// ============================================================================
// TYPES
// ============================================================================

interface SourceSearchResult {
  source: DataSourceConfig;
  result: UnifiedSearchResult | null;
  error: string | null;
}

interface SourceHealthReport {
  sourceId: string;
  sourceName: string;
  sourceType: DataSourceType;
  health: any;
  stats: any;
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

/**
 * Global multi-source manager instance
 */
export const multiSourceManager = new MultiSourceManager();