/**
 * Data Sources Configuration
 * Centralized configuration for all data sources
 */

import { DataSourceConfig } from '../types-multi-source';

/**
 * Default data source configurations
 */
export const defaultDataSourceConfigs: DataSourceConfig[] = [
  // SIBOM Scraping (highest priority - official data)
  {
    id: 'sibom_primary',
    type: 'sibom_scraping',
    name: 'SIBOM Official Bulletins',
    enabled: true,
    priority: 100, // Highest priority
    refreshInterval: 60, // 1 hour
    config: {
      type: 'sibom_scraping',
      baseUrl: 'https://sibom.slyt.gba.gob.ar',
      municipalities: [
        'Carlos Tejedor', 'Merlo', 'La Plata', 'Bahía Blanca',
        // Add more municipalities as needed
      ],
      maxConcurrency: 3,
      rateLimitMs: 3000
    }
  },

  // Manual Upload (medium priority - user content)
  {
    id: 'manual_upload_primary',
    type: 'manual_upload',
    name: 'User Uploaded Documents',
    enabled: true,
    priority: 50, // Medium priority
    config: {
      type: 'manual_upload',
      allowedMimeTypes: [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/json'
      ],
      maxFileSize: 10 * 1024 * 1024, // 10MB
      autoProcessing: true,
      storageLocation: 'local' // or 's3', 'gcs', etc.
    }
  },

  // Example: RSS Feed (disabled by default)
  {
    id: 'news_rss',
    type: 'rss_feed',
    name: 'Municipal News RSS',
    enabled: false, // Disabled by default
    priority: 20, // Lower priority
    refreshInterval: 30, // 30 minutes
    config: {
      type: 'rss_feed',
      feedUrl: 'https://example.com/municipal-news.rss',
      maxItems: 100,
      categories: ['news', 'announcements']
    }
  },

  // Example: API Integration (disabled by default)
  {
    id: 'external_api',
    type: 'api_integration',
    name: 'External Legal Database',
    enabled: false, // Disabled by default
    priority: 30,
    refreshInterval: 120, // 2 hours
    config: {
      type: 'api_integration',
      endpoint: 'https://api.example.com/legal-docs',
      apiKey: process.env.EXTERNAL_API_KEY,
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'SIBOM-Assistant/1.0'
      },
      rateLimit: {
        requestsPerMinute: 60,
        burstLimit: 10
      }
    }
  }
];

/**
 * Get configuration from environment variables
 */
export function getDataSourceConfigFromEnv(): DataSourceConfig[] {
  const configs = [...defaultDataSourceConfigs];

  // Override with environment variables
  const envConfig = process.env.DATA_SOURCES_CONFIG;
  if (envConfig) {
    try {
      const customConfigs = JSON.parse(envConfig);
      return customConfigs;
    } catch (error) {
      console.warn('[Config] Invalid DATA_SOURCES_CONFIG, using defaults:', error);
    }
  }

  // Individual environment overrides
  configs.forEach(config => {
    const envKey = `DATA_SOURCE_${config.id.toUpperCase()}_ENABLED`;
    if (process.env[envKey] !== undefined) {
      config.enabled = process.env[envKey] === 'true';
    }
  });

  return configs;
}

/**
 * Validate data source configuration
 */
export function validateDataSourceConfig(config: DataSourceConfig): string[] {
  const errors: string[] = [];

  if (!config.id) {
    errors.push('Missing required field: id');
  }

  if (!config.type) {
    errors.push('Missing required field: type');
  }

  if (!config.name) {
    errors.push('Missing required field: name');
  }

  if (typeof config.enabled !== 'boolean') {
    errors.push('Field "enabled" must be boolean');
  }

  if (typeof config.priority !== 'number' || config.priority < 0) {
    errors.push('Field "priority" must be a non-negative number');
  }

  if (config.refreshInterval !== undefined && 
      (typeof config.refreshInterval !== 'number' || config.refreshInterval <= 0)) {
    errors.push('Field "refreshInterval" must be a positive number');
  }

  if (!config.config) {
    errors.push('Missing required field: config');
  }

  // Type-specific validation
  switch (config.type) {
    case 'sibom_scraping':
      const sibomConfig = config.config as any;
      if (!sibomConfig.baseUrl) {
        errors.push('SIBOM config missing baseUrl');
      }
      if (!Array.isArray(sibomConfig.municipalities) || sibomConfig.municipalities.length === 0) {
        errors.push('SIBOM config missing municipalities array');
      }
      break;

    case 'manual_upload':
      const uploadConfig = config.config as any;
      if (!Array.isArray(uploadConfig.allowedMimeTypes) || uploadConfig.allowedMimeTypes.length === 0) {
        errors.push('Manual upload config missing allowedMimeTypes');
      }
      if (typeof uploadConfig.maxFileSize !== 'number' || uploadConfig.maxFileSize <= 0) {
        errors.push('Manual upload config invalid maxFileSize');
      }
      break;

    case 'api_integration':
      const apiConfig = config.config as any;
      if (!apiConfig.endpoint) {
        errors.push('API config missing endpoint');
      }
      break;
  }

  return errors;
}

/**
 * Get development configuration (with additional test sources)
 */
export function getDevelopmentConfig(): DataSourceConfig[] {
  const configs = getDataSourceConfigFromEnv();

  // Add development-only sources
  if (process.env.NODE_ENV === 'development') {
    configs.push({
      id: 'test_data',
      type: 'manual_upload',
      name: 'Test Data Source',
      enabled: true,
      priority: 10, // Low priority
      config: {
        type: 'manual_upload',
        allowedMimeTypes: ['application/json', 'text/plain'],
        maxFileSize: 1024 * 1024, // 1MB
        autoProcessing: true,
        storageLocation: 'memory'
      }
    });
  }

  return configs;
}

/**
 * Configuration presets for different deployment scenarios
 */
export const configPresets = {
  /**
   * Minimal configuration - SIBOM only
   */
  minimal: (): DataSourceConfig[] => [
    defaultDataSourceConfigs[0] // SIBOM only
  ],

  /**
   * Standard configuration - SIBOM + Manual Upload
   */
  standard: (): DataSourceConfig[] => [
    defaultDataSourceConfigs[0], // SIBOM
    defaultDataSourceConfigs[1]  // Manual Upload
  ],

  /**
   * Full configuration - All sources enabled
   */
  full: (): DataSourceConfig[] => 
    defaultDataSourceConfigs.map(config => ({ ...config, enabled: true })),

  /**
   * Demo configuration - Safe for public demos
   */
  demo: (): DataSourceConfig[] => [
    {
      ...defaultDataSourceConfigs[0],
      config: {
        ...defaultDataSourceConfigs[0].config,
        municipalities: ['Carlos Tejedor'] // Limited municipalities
      }
    },
    {
      ...defaultDataSourceConfigs[1],
      config: {
        ...defaultDataSourceConfigs[1].config,
        maxFileSize: 1024 * 1024 // 1MB limit for demo
      }
    }
  ]
};

/**
 * Get configuration based on environment
 */
export function getConfigForEnvironment(): DataSourceConfig[] {
  const env = process.env.NODE_ENV;
  const preset = process.env.DATA_SOURCES_PRESET;

  if (preset && preset in configPresets) {
    console.log(`[Config] Using preset: ${preset}`);
    return (configPresets as any)[preset]();
  }

  switch (env) {
    case 'development':
      return getDevelopmentConfig();
    case 'production':
      return getDataSourceConfigFromEnv();
    case 'test':
      return configPresets.minimal();
    default:
      return configPresets.standard();
  }
}