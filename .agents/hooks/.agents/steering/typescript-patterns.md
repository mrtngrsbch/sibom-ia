# typescript-patterns

## ⚠️ BASE EDITABLE

Este archivo fue copiado desde: `.kiro/steering/typescript-patterns.md`

**Puedes EDITAR este archivo** para agregar reglas específicas para agentes AI.

Para regenerar desde .kiro/:
```bash
python .agents/hooks/sync_from_kiro.py
```

---

---
inclusion: fileMatch
fileMatchPattern: '**/*.{ts,tsx}'
---

# TypeScript Engineering Patterns - SIBOM Frontend

## Type System Architecture

### 1. Centralized Type Definitions

**Observed Pattern:** `chatbot/src/lib/types.ts`
```typescript
// ✅ Centralized, exported interfaces
export interface SearchFilters {
  municipality?: string | null;
  type?: string;
  dateFrom?: string | null;
  dateTo?: string | null;
  limit?: number;
}

// ✅ Discriminated unions for type safety
export interface IndexEntry {
  id: string;
  municipality: string;
  type: 'ordenanza' | 'decreto' | 'boletin';  // Literal types
  documentTypes?: DocumentType[];             // Optional arrays
}
```

**Type Safety Standards:**
- **No `any` Types:** Eliminate all `any` usage except for justified edge cases
- **Strict Null Checks:** Use `string | null` instead of optional for explicit nullability
- **Literal Types:** Use string literals for enums (`'ordenanza' | 'decreto'`)
- **Branded Types:** Use branded types for IDs to prevent mixing different ID types
- **Immutable by Default:** Use `readonly` for arrays and object properties when appropriate

### 2. Advanced Type Patterns

**Conditional Types for API Responses:**
```typescript
// Conditional type based on search parameters
type SearchResponse<T extends SearchFilters> = 
  T['municipality'] extends string 
    ? { results: Document[]; municipality: string }
    : { results: Document[]; suggestedMunicipalities: string[] };

// Template literal types for dynamic keys
type FilterKey = `filter_${string}`;
type DynamicFilters = Record<FilterKey, string>;

// Utility types for partial updates
type PartialUpdate<T> = {
  [K in keyof T]?: T[K] extends object ? PartialUpdate<T[K]> : T[K];
};
```

**Engineering Requirements:**
- **Type-Level Programming:** Use conditional types to encode business logic at compile time
- **Template Literals:** Leverage template literal types for dynamic string patterns
- **Utility Types:** Create reusable utility types for common patterns
- **Mapped Types:** Use mapped types for transformations and partial updates

### 3. React Component Patterns

**Compound Component Pattern:**
```typescript
// chatbot/src/components/chat/ActiveFilters.tsx
interface ActiveFiltersProps {
  municipality: string | null;
  ordinanceType: DocumentType | 'all';
  dateFrom: string | null;
  dateTo: string | null;
  onRemoveFilter: (filterKey: keyof ChatFilters) => void;
  onShowAdvancedFilters: () => void;
}

// ✅ Explicit prop types with no optional props unless truly optional
export default function ActiveFilters({
  municipality,
  ordinanceType,
  dateFrom,
  dateTo,
  onRemoveFilter,
  onShowAdvancedFilters
}: ActiveFiltersProps) {
  // Component implementation
}
```

**Component Architecture Standards:**
- **Explicit Props:** No implicit prop spreading, all props explicitly typed
- **Callback Typing:** Use specific function signatures, not generic `Function`
- **Children Patterns:** Use `React.ReactNode` for children, `React.ComponentProps<'div'>` for HTML props
- **Generic Components:** Use generics for reusable components with type safety
- **Ref Forwarding:** Use `React.forwardRef` with proper typing for ref-forwarding components

### 4. State Management Patterns

**Immutable State Updates:**
```typescript
// chatbot/src/app/page.tsx
const handleRemoveFilter = useCallback((filterKey: keyof ChatFilters) => {
  setCurrentFilters(prev => ({
    ...prev,
    [filterKey]: filterKey === 'ordinanceType' ? 'all' : null
  }));
}, []);

// ✅ Type-safe state updates with discriminated unions
type FilterAction = 
  | { type: 'SET_MUNICIPALITY'; payload: string | null }
  | { type: 'SET_TYPE'; payload: DocumentType | 'all' }
  | { type: 'SET_DATE_RANGE'; payload: { from: string | null; to: string | null } }
  | { type: 'CLEAR_ALL' };

function filterReducer(state: ChatFilters, action: FilterAction): ChatFilters {
  switch (action.type) {
    case 'SET_MUNICIPALITY':
      return { ...state, municipality: action.payload };
    case 'SET_TYPE':
      return { ...state, ordinanceType: action.payload };
    case 'SET_DATE_RANGE':
      return { ...state, dateFrom: action.payload.from, dateTo: action.payload.to };
    case 'CLEAR_ALL':
      return { municipality: null, ordinanceType: 'all', dateFrom: null, dateTo: null };
    default:
      return state;
  }
}
```

**State Management Requirements:**
- **Immutable Updates:** Always return new objects, never mutate existing state
- **Discriminated Unions:** Use discriminated unions for action types
- **Type-Safe Reducers:** Ensure reducers handle all action types exhaustively
- **Callback Dependencies:** Always specify dependencies in `useCallback` and `useMemo`

### 5. Performance Optimization Patterns

**Memoization Strategy:**
```typescript
// chatbot/src/components/chat/ChatContainer.tsx
const markdownComponents = useMemo(() => ({
  a: ({ node, ...props }: any) => (
    <a {...props} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" />
  ),
  table: ({ node, ...props }: any) => (
    <table {...props} className="border-collapse border border-gray-300 my-4" />
  ),
  // ... other components
}), []); // Empty dependency array - components never change

const debouncedSaveHistory = useMemo(
  () => debounce((msgs: Message[]) => {
    localStorage.setItem('chat-history', JSON.stringify(msgs));
  }, 500),
  [] // Empty deps - debounce function is stable
);
```

**Performance Engineering Standards:**
- **Stable References:** Use `useMemo` with empty deps for stable object references
- **Debouncing:** Implement debouncing for expensive operations (localStorage, API calls)
- **React.memo:** Use `React.memo` for components that receive stable props
- **Lazy Loading:** Use `React.lazy` and `Suspense` for code splitting
- **Virtual Scrolling:** Implement virtual scrolling for large lists

### 6. Error Handling and Resilience

**Comprehensive Error Boundaries:**
```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ChatErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to monitoring service
    console.error('Chat Error Boundary caught an error:', error, errorInfo);
    
    // Update state with error info
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong in the chat.</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo.componentStack}
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Error Handling Requirements:**
- **Error Boundaries:** Wrap major UI sections in error boundaries
- **Graceful Degradation:** Provide meaningful fallback UI for errors
- **Error Logging:** Log errors to external monitoring (Sentry, LogRocket)
- **Recovery Mechanisms:** Provide user actions to recover from errors
- **Type-Safe Errors:** Use discriminated unions for different error types

### 7. API Integration Patterns

**Type-Safe API Client:**
```typescript
// API response types
interface APIResponse<T> {
  data: T;
  error?: string;
  metadata?: {
    timestamp: string;
    requestId: string;
  };
}

// Generic API client with proper error handling
class APIClient {
  private baseURL: string;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }
  
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        throw new APIError(`HTTP ${response.status}: ${response.statusText}`, response.status);
      }
      
      const data = await response.json();
      return { data };
      
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      throw new APIError(`Network error: ${error.message}`, 0);
    }
  }
}

// Custom error class for API errors
class APIError extends Error {
  constructor(message: string, public statusCode: number) {
    super(message);
    this.name = 'APIError';
  }
}
```

**API Integration Standards:**
- **Generic Response Types:** Use generic types for consistent API response structure
- **Custom Error Classes:** Create specific error classes for different error types
- **Request/Response Interceptors:** Implement interceptors for common functionality
- **Retry Logic:** Implement exponential backoff for transient failures
- **Type Guards:** Use type guards to validate API responses at runtime

### 8. Testing Patterns

**Component Testing with React Testing Library:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ActiveFilters from './ActiveFilters';

describe('ActiveFilters', () => {
  const defaultProps = {
    municipality: null,
    ordinanceType: 'all' as const,
    dateFrom: null,
    dateTo: null,
    onRemoveFilter: vi.fn(),
    onShowAdvancedFilters: vi.fn(),
  };

  it('should display municipality filter badge when municipality is set', () => {
    render(
      <ActiveFilters 
        {...defaultProps} 
        municipality="Carlos Tejedor" 
      />
    );
    
    expect(screen.getByText('Carlos Tejedor')).toBeInTheDocument();
    expect(screen.getByLabelText('Remove municipality filter')).toBeInTheDocument();
  });

  it('should call onRemoveFilter when filter badge is clicked', async () => {
    const onRemoveFilter = vi.fn();
    
    render(
      <ActiveFilters 
        {...defaultProps} 
        municipality="Carlos Tejedor"
        onRemoveFilter={onRemoveFilter}
      />
    );
    
    fireEvent.click(screen.getByLabelText('Remove municipality filter'));
    
    await waitFor(() => {
      expect(onRemoveFilter).toHaveBeenCalledWith('municipality');
    });
  });
});
```

**Testing Requirements:**
- **User-Centric Tests:** Test behavior from user perspective, not implementation details
- **Mock External Dependencies:** Mock API calls, localStorage, and other external dependencies
- **Accessibility Testing:** Test ARIA labels, keyboard navigation, and screen reader compatibility
- **Visual Regression Testing:** Use tools like Chromatic for visual regression testing
- **Property-Based Testing:** Use fast-check for property-based testing of complex logic

### 9. Configuration and Environment Management

**Type-Safe Environment Variables:**
```typescript
// Environment variable schema with validation
const envSchema = z.object({
  OPENROUTER_API_KEY: z.string().min(1, 'OpenRouter API key is required'),
  LLM_MODEL_PRIMARY: z.string().default('anthropic/claude-3.5-sonnet'),
  LLM_MODEL_ECONOMIC: z.string().default('google/gemini-flash-1.5'),
  GITHUB_DATA_REPO: z.string().optional(),
  GITHUB_DATA_BRANCH: z.string().default('main'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

// Type-safe environment configuration
export const env = envSchema.parse(process.env);

// Configuration object with computed values
export const config = {
  api: {
    openRouterKey: env.OPENROUTER_API_KEY,
    primaryModel: env.LLM_MODEL_PRIMARY,
    economicModel: env.LLM_MODEL_ECONOMIC,
  },
  data: {
    source: env.GITHUB_DATA_REPO ? 'github' : 'local',
    githubRepo: env.GITHUB_DATA_REPO,
    githubBranch: env.GITHUB_DATA_BRANCH,
  },
  isDevelopment: env.NODE_ENV === 'development',
  isProduction: env.NODE_ENV === 'production',
} as const;
```

**Configuration Standards:**
- **Schema Validation:** Use Zod or similar for runtime validation of environment variables
- **Type Safety:** Generate TypeScript types from validation schemas
- **Fail Fast:** Validate configuration at application startup
- **Immutable Config:** Use `as const` to make configuration immutable
- **Environment-Specific:** Support different configurations per environment

### 10. Code Organization and Module Structure

**Feature-Based Architecture:**
```
src/
├── components/           # Reusable UI components
│   ├── chat/            # Chat-specific components
│   ├── layout/          # Layout components
│   └── ui/              # Base UI components (shadcn/ui)
├── lib/                 # Business logic and utilities
│   ├── rag/             # RAG system modules
│   ├── types.ts         # Centralized type definitions
│   ├── constants.ts     # Application constants
│   └── utils.ts         # Utility functions
├── hooks/               # Custom React hooks
├── app/                 # Next.js app router pages
└── prompts/             # LLM prompts
```

**Module Organization Standards:**
- **Feature Colocation:** Group related components, hooks, and utilities together
- **Barrel Exports:** Use index.ts files for clean imports
- **Dependency Direction:** Dependencies should flow inward (UI → lib → utils)
- **Circular Dependencies:** Avoid circular dependencies between modules
- **Public API:** Clearly define public API surface for each module

---

## Implementation Checklist

When implementing new TypeScript modules in this project:

- [ ] Define explicit interfaces for all props and function parameters
- [ ] Use discriminated unions for complex state and action types
- [ ] Implement proper error boundaries for UI resilience
- [ ] Add comprehensive unit tests with React Testing Library
- [ ] Use `useMemo` and `useCallback` for performance optimization
- [ ] Validate environment variables with runtime schema validation
- [ ] Follow feature-based code organization
- [ ] Implement type-safe API clients with proper error handling
- [ ] Use branded types for domain-specific identifiers
- [ ] Add accessibility attributes and test keyboard navigation