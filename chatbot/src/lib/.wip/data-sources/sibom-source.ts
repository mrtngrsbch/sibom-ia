/**
 * SIBOM Data Source Implementation
 * Adapts current SIBOM scraping data to unified format
 */

import { BaseDataSource, SourceStats, HealthStatus } from './base-source';
import { 
  UnifiedDocument, 
  UnifiedSearchFilters, 
  UnifiedSearchResult,
  SIBOMSourceData,
  LegacyIndexEntry,
  SIBOMConfig
} from '../types-multi-source';
import { BM25Index, tokenize } from '../rag/bm25';
import { loadIndex, readDocumentContent } from '../rag/retriever';

/**
 * SIBOM data source implementation
 */
export class SIBOMDataSource extends BaseDataSource {
  private index: LegacyIndexEntry[] = [];
  private bm25Index?: BM25Index;
  private documentsCache = new Map<string, UnifiedDocument>();

  async initialize(): Promise<void> {
    try {
      console.log('[SIBOMSource] Initializing SIBOM data source...');
      
      // Load existing SIBOM index
      this.index = await loadIndex();
      
      // Build BM25 index for search
      await this.buildSearchIndex();
      
      this.isInitialized = true;
      console.log(`[SIBOMSource] ✅ Initialized with ${this.index.length} documents`);
      
    } catch (error) {
      console.error('[SIBOMSource] ❌ Failed to initialize:', error);
      throw error;
    }
  }

  async search(filters: UnifiedSearchFilters): Promise<UnifiedSearchResult> {
    if (!this.isInitialized || !this.bm25Index) {
      throw new Error('SIBOM source not initialized');
    }

    const startTime = Date.now();
    
    try {
      // Convert unified filters to legacy format
      const legacyFilters = this.convertFilters(filters);
      
      // Apply filters to index
      let filteredIndex = this.applyFilters(this.index, legacyFilters);
      
      // Perform BM25 search if query provided
      let searchResults: UnifiedDocument[] = [];
      
      if (filters.query) {
        const bm25Results = this.bm25Index.search(filters.query, filters.limit || 10);
        const relevantEntries = bm25Results.map(result => filteredIndex[result.index]);
        
        // Convert to unified documents
        searchResults = await Promise.all(
          relevantEntries.map(entry => this.convertToUnified(entry))
        );
      } else {
        // No query - return filtered results
        const limit = filters.limit || 10;
        const offset = filters.offset || 0;
        const slicedEntries = filteredIndex.slice(offset, offset + limit);
        
        searchResults = await Promise.all(
          slicedEntries.map(entry => this.convertToUnified(entry))
        );
      }

      const executionTime = Date.now() - startTime;

      return {
        documents: searchResults,
        totalCount: filteredIndex.length,
        facets: this.buildFacets(filteredIndex),
        searchMetadata: {
          query: filters.query || '',
          executionTimeMs: executionTime,
          totalSources: 1,
          sourcesQueried: ['sibom_scraping'],
          cacheHit: false
        }
      };

    } catch (error) {
      console.error('[SIBOMSource] Search error:', error);
      throw error;
    }
  }

  async getDocument(id: string): Promise<UnifiedDocument | null> {
    // Check cache first
    if (this.documentsCache.has(id)) {
      return this.documentsCache.get(id)!;
    }

    // Find in index
    const entry = this.index.find(e => e.id === id);
    if (!entry) {
      return null;
    }

    // Convert to unified format
    const document = await this.convertToUnified(entry);
    
    // Cache the result
    this.documentsCache.set(id, document);
    
    return document;
  }

  async getAllDocuments(offset = 0, limit = 100): Promise<UnifiedDocument[]> {
    const entries = this.index.slice(offset, offset + limit);
    return Promise.all(entries.map(entry => this.convertToUnified(entry)));
  }

  async refresh(): Promise<void> {
    console.log('[SIBOMSource] Refreshing SIBOM data...');
    
    // Clear caches
    this.documentsCache.clear();
    
    // Reload index
    this.index = await loadIndex();
    
    // Rebuild search index
    await this.buildSearchIndex();
    
    console.log(`[SIBOMSource] ✅ Refreshed with ${this.index.length} documents`);
  }

  async getStats(): Promise<SourceStats> {
    const categories = this.index.reduce((acc, entry) => {
      acc[entry.type] = (acc[entry.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalDocuments: this.index.length,
      lastUpdated: new Date().toISOString(),
      averageDocumentSize: 0, // TODO: Calculate from content
      categories,
      healthStatus: await this.healthCheck(),
      errorCount: 0,
    };
  }

  async validateConfig(): Promise<boolean> {
    const config = this.config.config as SIBOMConfig;
    return !!(config.baseUrl && config.municipalities?.length > 0);
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();
    
    try {
      // Simple health check - verify we have data
      if (this.index.length === 0) {
        return {
          status: 'unhealthy',
          message: 'No documents available',
          lastChecked: new Date().toISOString(),
          responseTimeMs: Date.now() - startTime
        };
      }

      return {
        status: 'healthy',
        message: `${this.index.length} documents available`,
        lastChecked: new Date().toISOString(),
        responseTimeMs: Date.now() - startTime
      };

    } catch (error) {
      return {
        status: 'unhealthy',
        message: `Health check failed: ${error.message}`,
        lastChecked: new Date().toISOString(),
        responseTimeMs: Date.now() - startTime
      };
    }
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  /**
   * Build BM25 search index
   */
  private async buildSearchIndex(): Promise<void> {
    console.log('[SIBOMSource] Building search index...');
    
    const documents = this.index.map(entry => {
      // Tokenize title and basic metadata for search
      const titleTokens = tokenize(entry.title);
      const typeTokens = tokenize(entry.type);
      const municipalityTokens = tokenize(entry.municipality);
      
      return [...titleTokens, ...typeTokens, ...municipalityTokens];
    });

    this.bm25Index = new BM25Index(documents);
    console.log('[SIBOMSource] ✅ Search index built');
  }

  /**
   * Convert legacy IndexEntry to UnifiedDocument
   */
  private async convertToUnified(entry: LegacyIndexEntry): Promise<UnifiedDocument> {
    // Try to get content (may fail for some documents)
    let content = '';
    let searchableText = entry.title;
    
    try {
      const docContent = await readDocumentContent(entry.filename);
      content = docContent.slice(0, 2000); // Limit content size
      searchableText = `${entry.title} ${content}`;
    } catch (error) {
      console.warn(`[SIBOMSource] Could not load content for ${entry.id}:`, error.message);
    }

    const sourceData: SIBOMSourceData = {
      sourceType: 'sibom_scraping',
      originalFilename: entry.filename,
      scrapingDate: new Date().toISOString(), // TODO: Get actual scraping date
      sibomUrl: entry.url,
    };

    return {
      // Base fields
      id: entry.id,
      sourceType: 'sibom_scraping',
      metadata: {
        name: 'SIBOM Scraping',
        description: 'Scraped from SIBOM official bulletins',
        confidence: 0.9, // High confidence for official sources
        language: 'es',
        region: 'Buenos Aires, Argentina'
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),

      // Document fields
      title: entry.title,
      content,
      category: 'legal',
      documentType: entry.type,
      
      // Legal specific
      officialNumber: entry.number,
      municipality: entry.municipality,
      jurisdiction: 'Buenos Aires',
      status: this.mapStatus(entry.status),
      
      // Temporal
      publishedDate: entry.date,
      
      // References
      url: entry.url,
      
      // Search
      searchableText,
      
      // Source data
      sourceData
    };
  }

  /**
   * Convert unified filters to legacy format
   */
  private convertFilters(filters: UnifiedSearchFilters) {
    return {
      municipality: filters.municipality,
      type: filters.documentType,
      dateFrom: filters.publishedAfter,
      dateTo: filters.publishedBefore,
      limit: filters.limit
    };
  }

  /**
   * Apply filters to index entries
   */
  private applyFilters(entries: LegacyIndexEntry[], filters: any): LegacyIndexEntry[] {
    return entries.filter(entry => {
      if (filters.municipality && entry.municipality !== filters.municipality) {
        return false;
      }
      if (filters.type && entry.type !== filters.type) {
        return false;
      }
      if (filters.dateFrom && entry.date < filters.dateFrom) {
        return false;
      }
      if (filters.dateTo && entry.date > filters.dateTo) {
        return false;
      }
      return true;
    });
  }

  /**
   * Build search facets
   */
  private buildFacets(entries: LegacyIndexEntry[]) {
    const categories = new Map<string, number>();
    const municipalities = new Map<string, number>();
    const documentTypes = new Map<string, number>();

    entries.forEach(entry => {
      categories.set('legal', (categories.get('legal') || 0) + 1);
      municipalities.set(entry.municipality, (municipalities.get(entry.municipality) || 0) + 1);
      documentTypes.set(entry.type, (documentTypes.get(entry.type) || 0) + 1);
    });

    return {
      categories: Array.from(categories.entries()).map(([value, count]) => ({ value, count })),
      sourceTypes: [{ value: 'sibom_scraping', count: entries.length }],
      municipalities: Array.from(municipalities.entries()).map(([value, count]) => ({ value, count })),
      documentTypes: Array.from(documentTypes.entries()).map(([value, count]) => ({ value, count })),
      status: [],
      languages: [{ value: 'es', count: entries.length }]
    };
  }

  /**
   * Map legacy status to unified status
   */
  private mapStatus(legacyStatus: string) {
    switch (legacyStatus.toLowerCase()) {
      case 'vigente': return 'active';
      case 'derogada': return 'repealed';
      case 'modificada': return 'superseded';
      default: return 'unknown';
    }
  }
}