/**
 * Base Data Source Interface
 * Abstract base class for all data sources
 */

import { 
  UnifiedDocument, 
  UnifiedSearchFilters, 
  UnifiedSearchResult,
  DataSourceType,
  DataSourceConfig 
} from '../types-multi-source';

/**
 * Abstract base class for all data sources
 */
export abstract class BaseDataSource {
  protected config: DataSourceConfig;
  protected isInitialized = false;

  constructor(config: DataSourceConfig) {
    this.config = config;
  }

  /**
   * Initialize the data source
   */
  abstract initialize(): Promise<void>;

  /**
   * Search documents in this data source
   */
  abstract search(filters: UnifiedSearchFilters): Promise<UnifiedSearchResult>;

  /**
   * Get a specific document by ID
   */
  abstract getDocument(id: string): Promise<UnifiedDocument | null>;

  /**
   * Get all documents (with pagination)
   */
  abstract getAllDocuments(
    offset?: number, 
    limit?: number
  ): Promise<UnifiedDocument[]>;

  /**
   * Refresh/sync data from source
   */
  abstract refresh(): Promise<void>;

  /**
   * Get source statistics
   */
  abstract getStats(): Promise<SourceStats>;

  /**
   * Validate source configuration
   */
  abstract validateConfig(): Promise<boolean>;

  /**
   * Health check for the data source
   */
  abstract healthCheck(): Promise<HealthStatus>;

  // ============================================================================
  // COMMON METHODS
  // ============================================================================

  /**
   * Get source configuration
   */
  getConfig(): DataSourceConfig {
    return { ...this.config };
  }

  /**
   * Get source type
   */
  getType(): DataSourceType {
    return this.config.type;
  }

  /**
   * Check if source is enabled
   */
  isEnabled(): boolean {
    return this.config.enabled;
  }

  /**
   * Get source priority
   */
  getPriority(): number {
    return this.config.priority;
  }

  /**
   * Check if source is initialized
   */
  isReady(): boolean {
    return this.isInitialized;
  }
}

/**
 * Source statistics
 */
export interface SourceStats {
  totalDocuments: number;
  lastUpdated: string;
  averageDocumentSize: number;
  categories: Record<string, number>;
  healthStatus: HealthStatus;
  errorCount: number;
  lastError?: string;
}

/**
 * Health status
 */
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message?: string;
  lastChecked: string;
  responseTimeMs?: number;
}

/**
 * Data source factory
 */
export class DataSourceFactory {
  private static sources = new Map<DataSourceType, typeof BaseDataSource>();

  /**
   * Register a data source implementation
   */
  static register(type: DataSourceType, sourceClass: typeof BaseDataSource) {
    this.sources.set(type, sourceClass);
  }

  /**
   * Create a data source instance
   */
  static create(config: DataSourceConfig): BaseDataSource {
    const SourceClass = this.sources.get(config.type);
    if (!SourceClass) {
      throw new Error(`Unknown data source type: ${config.type}`);
    }
    return new SourceClass(config);
  }

  /**
   * Get all registered source types
   */
  static getRegisteredTypes(): DataSourceType[] {
    return Array.from(this.sources.keys());
  }
}