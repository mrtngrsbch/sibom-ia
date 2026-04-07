# Estrategias de Manejo de Errores - SIBOM Scraper Assistant

## Arquitectura de Manejo de Errores

### 1. Frontend Next.js - Estrategias Implementadas

#### Error Boundaries React
**Ubicación:** `chatbot/src/components/chat/ChatContainer.tsx`
```typescript
// Error boundary implícito en useChat hook de Vercel AI SDK
const { messages, input, handleInputChange, handleSubmit, error, isLoading } = useChat({
  api: '/api/chat',
  onError: (error) => {
    console.error('Chat error:', error);
    // Error se propaga automáticamente al UI
  }
});

// Manejo de errores de UI
{error && (
  <div className="error-message bg-red-50 border border-red-200 rounded-lg p-4">
    <p className="text-red-800">Error: {error.message}</p>
  </div>
)}
```

#### Manejo de Errores de API
**Ubicación:** `chatbot/src/app/api/chat/route.ts:320-340`
```typescript
} catch (error: any) {
  console.error('[ChatAPI] Error fatal:', error);
  
  // Si es un error de autenticación de OpenRouter/LLM
  const errorMessage = error?.message || 'Error interno del servidor';
  const statusCode = error?.status || 500;

  return new Response(
    JSON.stringify({
      error: errorMessage,
      details: error?.data || error?.cause || String(error)
    }),
    {
      status: statusCode,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
```

#### Manejo de Errores de RAG
**Ubicación:** `chatbot/src/lib/rag/retriever.ts:150-170`
```typescript
// Error handling en fetchGitHubIndex()
try {
  const response = await fetch(url, {
    cache: 'force-cache',
    next: { revalidate: 3600 }
  });

  if (!response.ok) {
    throw new Error(`GitHub respondió con status ${response.status}`);
  }
  // ... procesamiento
} catch (error) {
  console.error('[RAG] ❌ Error descargando índice de GitHub:', error);
  throw error;
}

// Fallback con cache antiguo
} catch (error) {
  console.error('[RAG] ❌ Error cargando índice:', error);
  // Si falla GitHub, intentar con cache viejo si existe
  if (indexCache.length > 0) {
    console.warn('[RAG] ⚠️ Usando cache antiguo como fallback');
    return indexCache;
  }
  return [];
}
```

### 2. Backend Python - Estrategias Implementadas

#### Rate Limiting y Retry Logic
**Ubicación:** `python-cli/sibom_scraper.py:180-220`
```python
async def _make_request_with_retry(self, prompt: str, max_retries: int = 3) -> str:
    """Hace request con retry automático y rate limiting"""
    
    for attempt in range(max_retries):
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            response = await self.client.chat.completions.create(
                model="google/gemini-2.0-flash-exp",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            if "429" in str(e):  # Rate limit
                wait_time = 30 * (2 ** attempt)  # Exponential backoff
                self.console.print(f"[yellow]Rate limit alcanzado. Esperando {wait_time}s...[/yellow]")
                await asyncio.sleep(wait_time)
                continue
            elif attempt == max_retries - 1:
                raise e
            else:
                self.console.print(f"[red]Error en intento {attempt + 1}: {e}[/red]")
                await asyncio.sleep(5)
```

#### Validación de JSON
**Ubicación:** `python-cli/sibom_scraper.py:240-260`
```python
def _extract_json(self, text: str) -> str:
    """Extrae JSON limpiando markdown code blocks"""
    cleaned = text.strip()
    
    # Limpiar markdown
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()

def _parse_json_safely(self, json_str: str) -> dict:
    """Parse JSON con manejo de errores"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        self.console.print(f"[red]Error parseando JSON: {e}[/red]")
        self.console.print(f"[red]Contenido: {json_str[:200]}...[/red]")
        return {}
```

### 3. Patrones de Error Handling por Categoría

#### Errores de Red/Conectividad
```typescript
// Frontend: Timeout y retry
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000);

try {
  const response = await fetch('/api/chat', {
    signal: controller.signal,
    // ... config
  });
} catch (error) {
  if (error.name === 'AbortError') {
    throw new Error('Timeout: La consulta tardó demasiado');
  }
  throw error;
} finally {
  clearTimeout(timeoutId);
}
```

```python
# Backend: Retry con backoff exponencial
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(session, url):
    async with session.get(url, timeout=30) as response:
        if response.status >= 400:
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status
            )
        return await response.text()
```

#### Errores de Validación de Datos
```typescript
// Frontend: Validación con Zod
import { z } from 'zod';

const MessageSchema = z.object({
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string().min(1),
  timestamp: z.string().datetime().optional()
});

try {
  const validatedMessage = MessageSchema.parse(rawMessage);
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error('Mensaje inválido:', error.errors);
    throw new Error('Formato de mensaje inválido');
  }
}
```

#### Errores de LLM/OpenRouter
```typescript
// Frontend: Manejo específico de errores de OpenRouter
export async function POST(req: Request) {
  try {
    const result = streamText({
      model: openrouter(modelId),
      // ... config
    });
    
    return result.toDataStreamResponse({
      data,
      getErrorMessage: (error: any) => {
        // Errores específicos de OpenRouter
        if (error.status === 401) {
          return 'API Key inválida o expirada';
        }
        if (error.status === 429) {
          return 'Límite de rate alcanzado. Intenta en unos minutos.';
        }
        if (error.status === 402) {
          return 'Créditos insuficientes en OpenRouter';
        }
        return error?.message || 'Error en el modelo de IA';
      }
    });
  } catch (streamError: any) {
    // Error crítico al iniciar stream
    return new Response(
      JSON.stringify({
        error: 'Error al conectar con el modelo de IA',
        details: streamError.message
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
```

### 4. Logging y Monitoreo

#### Logging Estructurado
```typescript
// Frontend: Console logging con contexto
console.log(`[ChatAPI] Nueva petición recibida`);
console.log(`[ChatAPI] API Key detectada (longitud: ${apiKey.length})`);
console.log(`[ChatAPI] Consulta: "${query.slice(0, 50)}..."`);
console.log(`[ChatAPI] Necesita RAG: ${shouldSearch} (isFAQ: ${isFAQ})`);

// Logging de performance
const startTime = Date.now();
// ... operación
const duration = Date.now() - startTime;
console.log(`[RAG] Query completada en ${duration}ms`);
```

```python
# Backend: Rich console con colores
from rich.console import Console
from rich.progress import Progress

console = Console()

# Logging con colores
console.print(f"[green]✅ Procesando boletín {bulletin_num}[/green]")
console.print(f"[yellow]⚠️ Rate limit alcanzado[/yellow]")
console.print(f"[red]❌ Error: {error_message}[/red]")

# Progress bars
with Progress() as progress:
    task = progress.add_task("Procesando boletines...", total=total_bulletins)
    # ... procesamiento
    progress.update(task, advance=1)
```

### 5. Graceful Degradation

#### Fallbacks en RAG
```typescript
// Si falla GitHub, usar cache local
export async function loadIndex(): Promise<IndexEntry[]> {
  try {
    const data = useGitHub() 
      ? await fetchGitHubIndex()
      : await readLocalIndex();
    
    indexCache = data;
    return indexCache;
  } catch (error) {
    console.error('[RAG] ❌ Error cargando índice:', error);
    
    // Fallback: usar cache antiguo si existe
    if (indexCache.length > 0) {
      console.warn('[RAG] ⚠️ Usando cache antiguo como fallback');
      return indexCache;
    }
    
    // Último recurso: array vacío
    return [];
  }
}
```

#### Respuestas de Emergencia
```typescript
// Si falla completamente el RAG
if (index.length === 0) {
  return { 
    context: 'Sistema temporalmente no disponible. Intenta nuevamente en unos minutos.', 
    sources: [] 
  };
}
```

### 6. User Experience durante Errores

#### Estados de Loading y Error
```typescript
// Componente con estados claros
{isLoading && (
  <div className="flex items-center space-x-2">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
    <span>Consultando normativas...</span>
  </div>
)}

{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <div className="flex">
      <AlertCircle className="h-5 w-5 text-red-400" />
      <div className="ml-3">
        <h3 className="text-sm font-medium text-red-800">
          Error en la consulta
        </h3>
        <p className="mt-1 text-sm text-red-700">
          {error.message}
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-2 text-sm text-red-600 underline"
        >
          Reintentar
        </button>
      </div>
    </div>
  </div>
)}
```

### 7. Métricas y Alertas

#### Tracking de Errores
```typescript
// Métricas básicas en memoria
interface ErrorMetrics {
  totalErrors: number;
  errorsByType: Record<string, number>;
  lastError: Date | null;
}

const errorMetrics: ErrorMetrics = {
  totalErrors: 0,
  errorsByType: {},
  lastError: null
};

function trackError(error: Error, type: string) {
  errorMetrics.totalErrors++;
  errorMetrics.errorsByType[type] = (errorMetrics.errorsByType[type] || 0) + 1;
  errorMetrics.lastError = new Date();
  
  // Log para monitoreo externo
  console.error(`[METRICS] Error ${type}:`, error.message);
}
```

## Principios de Error Handling

### 1. Fail Fast, Recover Gracefully
- Detectar errores temprano en el pipeline
- Proporcionar fallbacks útiles cuando sea posible
- No ocultar errores críticos del usuario

### 2. Contexto Rico en Errores
- Incluir información suficiente para debugging
- Logs estructurados con timestamps y contexto
- Stack traces en desarrollo, mensajes amigables en producción

### 3. User-Centric Error Messages
- Mensajes claros sobre qué salió mal
- Acciones sugeridas para el usuario
- Evitar jerga técnica en mensajes de usuario

### 4. Monitoring y Observabilidad
- Logs centralizados con niveles apropiados
- Métricas de error rates y tipos
- Alertas para errores críticos

### 5. Testing de Error Scenarios
- Unit tests para casos de error
- Integration tests con servicios externos fallando
- Chaos engineering para resilencia

## Checklist de Error Handling

- [ ] ✅ Todos los async/await tienen try-catch
- [ ] ✅ Errores de red tienen retry logic
- [ ] ✅ Validación de entrada con schemas
- [ ] ✅ Fallbacks para servicios externos
- [ ] ✅ Mensajes de error user-friendly
- [ ] ✅ Logging estructurado implementado
- [ ] ⏳ Error boundaries en componentes React
- [ ] ⏳ Métricas de error tracking
- [ ] ⏳ Tests de error scenarios
- [ ] ⏳ Alertas para errores críticos