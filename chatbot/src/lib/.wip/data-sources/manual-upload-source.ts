/**
 * Manual Upload Data Source Implementation
 * Handles user-uploaded documents (PDFs, Word docs, etc.)
 */

import { BaseDataSource, SourceStats, HealthStatus } from './base-source';
import { 
  UnifiedDocument, 
  UnifiedSearchFilters, 
  UnifiedSearchResult,
  ManualUploadSourceData,
  ManualUploadConfig
} from '../types-multi-source';
import { BM25Index, tokenize } from '../rag/bm25';

/**
 * Manual upload data source implementation
 */
export class ManualUploadDataSource extends BaseDataSource {
  private documents: UnifiedDocument[] = [];
  private bm25Index?: BM25Index;
  private storageAdapter: StorageAdapter;

  constructor(config: any) {
    super(config);
    this.storageAdapter = new LocalStorageAdapter(); // Default to localStorage
  }

  async initialize(): Promise<void> {
    try {
      console.log('[ManualUpload] Initializing manual upload source...');
      
      // Load existing documents from storage
      this.documents = await this.storageAdapter.loadDocuments();
      
      // Build search index
      await this.buildSearchIndex();
      
      this.isInitialized = true;
      console.log(`[ManualUpload] ✅ Initialized with ${this.documents.length} documents`);
      
    } catch (error) {
      console.error('[ManualUpload] ❌ Failed to initialize:', error);
      throw error;
    }
  }

  async search(filters: UnifiedSearchFilters): Promise<UnifiedSearchResult> {
    if (!this.isInitialized) {
      throw new Error('Manual upload source not initialized');
    }

    const startTime = Date.now();
    
    try {
      // Apply filters
      let filteredDocs = this.applyFilters(this.documents, filters);
      
      // Perform search if query provided
      if (filters.query && this.bm25Index) {
        const bm25Results = this.bm25Index.search(filters.query, filters.limit || 10);
        filteredDocs = bm25Results.map(result => filteredDocs[result.index]);
      } else {
        // No query - return paginated results
        const limit = filters.limit || 10;
        const offset = filters.offset || 0;
        filteredDocs = filteredDocs.slice(offset, offset + limit);
      }

      const executionTime = Date.now() - startTime;

      return {
        documents: filteredDocs,
        totalCount: this.documents.length,
        facets: this.buildFacets(this.documents),
        searchMetadata: {
          query: filters.query || '',
          executionTimeMs: executionTime,
          totalSources: 1,
          sourcesQueried: ['manual_upload'],
          cacheHit: false
        }
      };

    } catch (error) {
      console.error('[ManualUpload] Search error:', error);
      throw error;
    }
  }

  async getDocument(id: string): Promise<UnifiedDocument | null> {
    return this.documents.find(doc => doc.id === id) || null;
  }

  async getAllDocuments(offset = 0, limit = 100): Promise<UnifiedDocument[]> {
    return this.documents.slice(offset, offset + limit);
  }

  async refresh(): Promise<void> {
    console.log('[ManualUpload] Refreshing manual upload data...');
    
    // Reload from storage
    this.documents = await this.storageAdapter.loadDocuments();
    
    // Rebuild search index
    await this.buildSearchIndex();
    
    console.log(`[ManualUpload] ✅ Refreshed with ${this.documents.length} documents`);
  }

  async getStats(): Promise<SourceStats> {
    const categories = this.documents.reduce((acc, doc) => {
      acc[doc.category] = (acc[doc.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalDocuments: this.documents.length,
      lastUpdated: new Date().toISOString(),
      averageDocumentSize: this.calculateAverageSize(),
      categories,
      healthStatus: await this.healthCheck(),
      errorCount: 0,
    };
  }

  async validateConfig(): Promise<boolean> {
    const config = this.config.config as ManualUploadConfig;
    return !!(config.allowedMimeTypes?.length > 0 && config.maxFileSize > 0);
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();
    
    try {
      // Check storage adapter health
      const isStorageHealthy = await this.storageAdapter.healthCheck();
      
      if (!isStorageHealthy) {
        return {
          status: 'unhealthy',
          message: 'Storage adapter unhealthy',
          lastChecked: new Date().toISOString(),
          responseTimeMs: Date.now() - startTime
        };
      }

      return {
        status: 'healthy',
        message: `${this.documents.length} uploaded documents available`,
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
  // PUBLIC METHODS (SPECIFIC TO MANUAL UPLOAD)
  // ============================================================================

  /**
   * Upload a new document
   */
  async uploadDocument(
    file: File, 
    metadata: Partial<UnifiedDocument>,
    userId: string
  ): Promise<UnifiedDocument> {
    const config = this.config.config as ManualUploadConfig;
    
    // Validate file
    this.validateFile(file, config);
    
    // Extract content based on file type
    const content = await this.extractContent(file);
    
    // Create unified document
    const sourceData: ManualUploadSourceData = {
      sourceType: 'manual_upload',
      originalFilename: file.name,
      uploadedBy: userId,
      uploadDate: new Date().toISOString(),
      fileSize: file.size,
      mimeType: file.type,
    };

    const document: UnifiedDocument = {
      id: this.generateId(),
      sourceType: 'manual_upload',
      metadata: {
        name: 'Manual Upload',
        description: `Uploaded by ${userId}`,
        confidence: 0.8, // Medium confidence for user uploads
        language: metadata.metadata?.language || 'es',
        ...metadata.metadata
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      
      title: metadata.title || file.name,
      content,
      category: metadata.category || 'other',
      documentType: metadata.documentType,
      
      searchableText: `${metadata.title || file.name} ${content}`,
      
      sourceData,
      ...metadata
    };

    // Save to storage
    await this.storageAdapter.saveDocument(document);
    
    // Add to in-memory collection
    this.documents.push(document);
    
    // Rebuild search index
    await this.buildSearchIndex();
    
    console.log(`[ManualUpload] ✅ Uploaded document: ${document.title}`);
    
    return document;
  }

  /**
   * Delete a document
   */
  async deleteDocument(id: string): Promise<boolean> {
    const index = this.documents.findIndex(doc => doc.id === id);
    if (index === -1) {
      return false;
    }

    // Remove from storage
    await this.storageAdapter.deleteDocument(id);
    
    // Remove from memory
    this.documents.splice(index, 1);
    
    // Rebuild search index
    await this.buildSearchIndex();
    
    console.log(`[ManualUpload] ✅ Deleted document: ${id}`);
    
    return true;
  }

  /**
   * Update document metadata
   */
  async updateDocument(id: string, updates: Partial<UnifiedDocument>): Promise<UnifiedDocument | null> {
    const document = this.documents.find(doc => doc.id === id);
    if (!document) {
      return null;
    }

    // Apply updates
    Object.assign(document, updates, {
      updatedAt: new Date().toISOString()
    });

    // Save to storage
    await this.storageAdapter.saveDocument(document);
    
    // Rebuild search index if content changed
    if (updates.content || updates.title) {
      await this.buildSearchIndex();
    }
    
    return document;
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private async buildSearchIndex(): Promise<void> {
    if (this.documents.length === 0) {
      this.bm25Index = undefined;
      return;
    }

    console.log('[ManualUpload] Building search index...');
    
    const tokenizedDocs = this.documents.map(doc => 
      tokenize(doc.searchableText)
    );

    this.bm25Index = new BM25Index(tokenizedDocs);
    console.log('[ManualUpload] ✅ Search index built');
  }

  private applyFilters(docs: UnifiedDocument[], filters: UnifiedSearchFilters): UnifiedDocument[] {
    return docs.filter(doc => {
      if (filters.category && doc.category !== filters.category) return false;
      if (filters.documentType && doc.documentType !== filters.documentType) return false;
      if (filters.publishedAfter && doc.publishedDate && doc.publishedDate < filters.publishedAfter) return false;
      if (filters.publishedBefore && doc.publishedDate && doc.publishedDate > filters.publishedBefore) return false;
      if (filters.language && doc.metadata.language !== filters.language) return false;
      return true;
    });
  }

  private buildFacets(docs: UnifiedDocument[]) {
    const categories = new Map<string, number>();
    const documentTypes = new Map<string, number>();
    const languages = new Map<string, number>();

    docs.forEach(doc => {
      categories.set(doc.category, (categories.get(doc.category) || 0) + 1);
      if (doc.documentType) {
        documentTypes.set(doc.documentType, (documentTypes.get(doc.documentType) || 0) + 1);
      }
      if (doc.metadata.language) {
        languages.set(doc.metadata.language, (languages.get(doc.metadata.language) || 0) + 1);
      }
    });

    return {
      categories: Array.from(categories.entries()).map(([value, count]) => ({ value, count })),
      sourceTypes: [{ value: 'manual_upload', count: docs.length }],
      municipalities: [],
      documentTypes: Array.from(documentTypes.entries()).map(([value, count]) => ({ value, count })),
      status: [],
      languages: Array.from(languages.entries()).map(([value, count]) => ({ value, count }))
    };
  }

  private validateFile(file: File, config: ManualUploadConfig): void {
    if (file.size > config.maxFileSize) {
      throw new Error(`File too large: ${file.size} bytes (max: ${config.maxFileSize})`);
    }

    if (!config.allowedMimeTypes.includes(file.type)) {
      throw new Error(`File type not allowed: ${file.type}`);
    }
  }

  private async extractContent(file: File): Promise<string> {
    // Simple text extraction - in production, use proper libraries
    if (file.type === 'text/plain') {
      return await file.text();
    }
    
    if (file.type === 'application/json') {
      return await file.text();
    }
    
    // For other types, return filename as placeholder
    // TODO: Implement PDF, Word, etc. extraction
    return `[Content from ${file.name}]`;
  }

  private calculateAverageSize(): number {
    if (this.documents.length === 0) return 0;
    const totalSize = this.documents.reduce((sum, doc) => sum + doc.content.length, 0);
    return Math.round(totalSize / this.documents.length);
  }

  private generateId(): string {
    return `manual_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// ============================================================================
// STORAGE ADAPTER INTERFACE
// ============================================================================

/**
 * Storage adapter interface
 */
interface StorageAdapter {
  loadDocuments(): Promise<UnifiedDocument[]>;
  saveDocument(document: UnifiedDocument): Promise<void>;
  deleteDocument(id: string): Promise<void>;
  healthCheck(): Promise<boolean>;
}

/**
 * Local storage adapter (for development/demo)
 */
class LocalStorageAdapter implements StorageAdapter {
  private readonly STORAGE_KEY = 'manual_upload_documents';

  async loadDocuments(): Promise<UnifiedDocument[]> {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('[LocalStorageAdapter] Failed to load documents:', error);
      return [];
    }
  }

  async saveDocument(document: UnifiedDocument): Promise<void> {
    try {
      const documents = await this.loadDocuments();
      const existingIndex = documents.findIndex(doc => doc.id === document.id);
      
      if (existingIndex >= 0) {
        documents[existingIndex] = document;
      } else {
        documents.push(document);
      }
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(documents));
    } catch (error) {
      console.error('[LocalStorageAdapter] Failed to save document:', error);
      throw error;
    }
  }

  async deleteDocument(id: string): Promise<void> {
    try {
      const documents = await this.loadDocuments();
      const filtered = documents.filter(doc => doc.id !== id);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('[LocalStorageAdapter] Failed to delete document:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      // Test localStorage availability
      const testKey = 'health_check_test';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch (error) {
      return false;
    }
  }
}