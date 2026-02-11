# Métricas de Éxito Específicas - SIBOM Scraper Assistant

**Fecha:** 2026-02-06
**Versión:** 1.0.0
**Autor:** Arquitecto de Software Senior (MIT/Stanford Engineering Perspective)
**Estado:** 📋 Métricas Definidas

---

## 📋 Resumen Ejecutivo

Este documento detalla las **métricas de éxito específicas** para medir el progreso y el impacto de las mejoras propuestas en los documentos de planificación existentes. Cada métrica incluye: definición, método de medición, objetivo actual, objetivo final, y plan de acción.

### Principios de Métricas

1. **SMART:** Específicas, Medibles, Alcanzables, Relevantes, Temporales
2. **Accionables:** Cada métrica tiene un plan de acción claro
3. **Rastreables:** Todas las métricas pueden ser monitoreadas automáticamente
4. **Priorizadas:** Enfocadas en impacto de negocio y valor para el usuario

---

## 1. Métricas Técnicas

### 1.1 Test Coverage

#### Definición
Porcentaje de código cubierto por tests automatizados (unitarios, integración, E2E).

#### Método de Medición
```bash
# Python
cd python-cli
pytest --cov=. --cov-report=term-missing

# TypeScript
cd chatbot
npm run test:coverage
```

#### Objetivos

| Métrica                             | Actual | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ----------------------------------- | ------ | --------------- | --------------- | -------------- |
| **Python Unit Coverage**            | ~30%   | >60%            | >75%            | >80%           |
| **Python Integration Coverage**     | ~20%   | >40%            | >60%            | >70%           |
| **TypeScript Unit Coverage**        | ~40%   | >60%            | >75%            | >80%           |
| **TypeScript Integration Coverage** | ~30%   | >50%            | >65%            | >70%           |
| **E2E Coverage**                    | 0%     | >20%            | >30%            | >40%           |
| **Total Coverage**                  | ~40%   | >60%            | >80%            | >80%           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar pytest para Python
- Implementar vitest para TypeScript
- Crear estructura de tests
- Objetivo: >60% cobertura total

**Fase 3 (Mes 3-4):**
- Añadir tests de integración
- Implementar mocks para APIs externas
- Crear fixtures de datos
- Objetivo: >80% cobertura total

**Fase 5 (Mes 7-8):**
- Implementar E2E tests con Playwright
- Añadir tests de performance
- Configurar reports automáticos
- Objetivo: >80% cobertura total

#### Métricas de Éxito

- Coverage reports generados automáticamente
- Integración con CI/CD
- Thresholds configurados para quality gates
- Dashboard de coverage en GitHub

### 1.2 CI/CD Performance

#### Definición
Tiempo de ejecución del pipeline de CI/CD desde push hasta deployment.

#### Método de Medición
```yaml
# GitHub Actions logs
- Checkout: ~10s
- Setup: ~30s
- Install dependencies: ~2min
- Run tests: ~3min
- Build: ~2min
- Deploy: ~1min
Total: ~10min
```

#### Objetivos

| Métrica                     | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| --------------------------- | ----------- | --------------- | --------------- | -------------- |
| **CI Execution Time**       | N/A         | <10min          | <8min           | <5min          |
| **CD Execution Time**       | Manual      | <10min          | <5min           | <2min          |
| **Total Pipeline Time**     | Manual      | <20min          | <13min          | <7min          |
| **Build Success Rate**      | Desconocido | >95%            | >98%            | >99%           |
| **Test Success Rate**       | Desconocido | >95%            | >98%            | >99%           |
| **Deployment Success Rate** | Manual      | >95%            | >98%            | >99%           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar GitHub Actions básico
- Configurar cache de dependencias
- Paralelizar jobs de testing
- Objetivo: <10min CI time

**Fase 3 (Mes 3-4):**
- Optimizar build de Next.js
- Implementar caching agresivo
- Paralelizar E2E tests
- Objetivo: <8min CI time

**Fase 5 (Mes 7-8):**
- Implementar deployment canary
- Optimizar scripts de deployment
- Implementar rollback automático
- Objetivo: <5min total pipeline time

#### Métricas de Éxito

- Dashboard de CI/CD en GitHub
- Alertas automáticas de fallos
- Reports de performance
- Integración con Slack/Discord

### 1.3 Code Quality

#### Definición
Número de errores de linting, type checking, y code smells.

#### Método de Medición
```bash
# Python
cd python-cli
ruff check .  # Linting
black --check .  # Formatting
mypy .  # Type checking

# TypeScript
cd chatbot
npm run lint  # ESLint
npm run type-check  # TypeScript
npm run format:check  # Prettier
```

#### Objetivos

| Métrica                       | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ----------------------------- | ----------- | --------------- | --------------- | -------------- |
| **Python Linting Errors**     | Desconocido | 0               | 0               | 0              |
| **Python Type Errors**        | Desconocido | 0               | 0               | 0              |
| **Python Code Smells**        | Desconocido | <10             | <5              | 0              |
| **TypeScript Linting Errors** | 0           | 0               | 0               | 0              |
| **TypeScript Type Errors**    | 0           | 0               | 0               | 0              |
| **TypeScript Code Smells**    | Desconocido | <10             | <5              | 0              |
| **Total Code Quality Score**  | Desconocido | >90/100         | >95/100         | >98/100        |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Configurar pre-commit hooks
- Implementar ruff (Python)
- Configurar ESLint + Prettier (TypeScript)
- Objetivo: 0 errores de calidad

**Fase 3 (Mes 3-4):**
- Añadir reglas de linting más estrictas
- Implementar SonarQube
- Configurar quality gates en CI/CD
- Objetivo: >95/100 quality score

**Fase 5 (Mes 7-8):**
- Refactorizar código complejo
- Eliminar code smells
- Optimizar complejidad ciclomática
- Objetivo: >98/100 quality score

#### Métricas de Éxito

- Pre-commit hooks bloqueando commits con errores
- Quality gates en CI/CD
- Dashboard de SonarQube
- Reports de calidad en PRs

### 1.4 Performance

#### Definición
Métricas de rendimiento de la aplicación: latencia, throughput, resource usage.

#### Método de Medición

**Frontend:**
```typescript
// chatbot/src/lib/metrics.ts
export class PerformanceMetrics {
  async measurePageLoad() {
    const navigation = performance.getEntriesByType('navigation')[0];
    return {
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
      loadComplete: navigation.loadEventEnd - navigation.fetchStart,
      firstPaint: navigation.responseStart - navigation.fetchStart,
    };
  }

  async measureAPICall(url: string) {
    const start = performance.now();
    const response = await fetch(url);
    const end = performance.now();
    return {
      duration: end - start,
      status: response.status,
      url,
    };
  }
}
```

**Backend:**
```python
# python-cli/metrics.py
import time
import psutil

class PerformanceMetrics:
    def measure_scraping_time(self, url: str):
        start = time.time()
        # ... scraping logic
        end = time.time()
        return end - start

    def measure_memory_usage(self):
        process = psutil.Process()
        return {
            'rss_mb': process.memory_info().rss / 1024 / 1024,
            'vms_mb': process.memory_info().vms / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
        }
```

#### Objetivos

| Métrica                     | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| --------------------------- | ----------- | --------------- | --------------- | -------------- |
| **Page Load Time (p95)**    | Desconocido | <3s             | <2s             | <1.5s          |
| **API Response Time (p95)** | Desconocido | <2s             | <1.5s           | <1s            |
| **Time to Interactive**     | Desconocido | <5s             | <3s             | <2s            |
| **First Contentful Paint**  | Desconocido | <2s             | <1.5s           | <1s            |
| **Lighthouse Performance**  | ~75         | >80             | >85             | >95            |
| **Bundle Size**             | ~500KB      | <400KB          | <350KB          | <300KB         |
| **Python Memory Usage**     | Desconocido | <1GB            | <512MB          | <256MB         |
| **Python CPU Usage**        | Desconocido | <70%            | <50%            | <30%           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar métricas de performance
- Configurar Lighthouse CI
- Optimizar bundle size
- Objetivo: >80 Lighthouse score

**Fase 3 (Mes 3-4):**
- Implementar lazy loading
- Optimizar imágenes
- Implementar code splitting
- Objetivo: >85 Lighthouse score

**Fase 5 (Mes 7-8):**
- Optimizar queries a Qdrant
- Implementar prefetching
- Optimizar embeddings
- Objetivo: >95 Lighthouse score

#### Métricas de Éxito

- Dashboard de performance en Vercel
- Lighthouse reports en PRs
- Alertas de degradación
- Reports de resource usage

---

## 2. Métricas de Producto

### 2.1 User Engagement

#### Definición
Métricas de engagement de usuarios: DAU, queries por día, tiempo de sesión.

#### Método de Medición

```typescript
// chatbot/src/lib/analytics.ts
export class UserAnalytics {
  async trackQuery(query: string, userId?: string) {
    await fetch('/api/analytics/track', {
      method: 'POST',
      body: JSON.stringify({
        event: 'query',
        properties: {
          query,
          userId,
          timestamp: new Date().toISOString(),
        },
      }),
    });
  }

  async getDailyStats(date: string) {
    const response = await fetch(`/api/analytics/daily?date=${date}`);
    return response.json();
  }
}
```

#### Objetivos

| Métrica                      | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ---------------------------- | ----------- | --------------- | --------------- | -------------- |
| **DAU (Daily Active Users)** | Desconocido | >50             | >200            | >1000          |
| **Queries per Day**          | Desconocido | >200            | >1000           | >5000          |
| **Average Session Duration** | Desconocido | >2min           | >5min           | >10min         |
| **Queries per Session**      | Desconocido | >2              | >5              | >10            |
| **User Retention (7d)**      | Desconocido | >30%            | >40%            | >50%           |
| **User Retention (30d)**     | Desconocido | >20%            | >30%            | >40%           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar tracking de analytics
- Configurar Google Analytics o Plausible
- Crear dashboard básico
- Objetivo: >50 DAU

**Fase 3 (Mes 3-4):**
- Implementar eventos de tracking
- Crear funnels de usuario
- Añadir cohort analysis
- Objetivo: >200 DAU

**Fase 5 (Mes 7-8):**
- Implementar user segmentation
- Añadir personalización
- Implementar recomendaciones
- Objetivo: >1000 DAU

#### Métricas de Éxito

- Dashboard de analytics en Vercel
- Reports diarios/semanales
- Alertas de anomalías
- Integración con Slack/Discord

### 2.2 User Satisfaction

#### Definición
Satisfacción del usuario medida a través de surveys, feedback, y métricas implícitas.

#### Método de Medición

```typescript
// chatbot/src/components/chat/FeedbackForm.tsx
export function FeedbackForm() {
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');

  const handleSubmit = async () => {
    await fetch('/api/feedback', {
      method: 'POST',
      body: JSON.stringify({
        rating,
        feedback,
        timestamp: new Date().toISOString(),
      }),
    });
  };

  return (
    <div>
      <h3>¿Fue útil esta respuesta?</h3>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => setRating(star)}
          className={star <= rating ? 'text-yellow-500' : 'text-gray-300'}
        >
          ★
        </button>
      ))}
      <textarea
        placeholder="Cuéntanos más..."
        onChange={(e) => setFeedback(e.target.value)}
      />
      <button onClick={handleSubmit}>Enviar</button>
    </div>
  );
}
```

#### Objetivos

| Métrica                      | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ---------------------------- | ----------- | --------------- | --------------- | -------------- |
| **Average Rating**           | Desconocido | >3.0/5          | >4.0/5          | >4.5/5         |
| **Feedback Rate**            | Desconocido | >5%             | >10%            | >15%           |
| **Positive Feedback %**      | Desconocido | >70%            | >80%            | >85%           |
| **Negative Feedback %**      | Desconocido | <10%            | <5%             | <3%            |
| **NPS (Net Promoter Score)** | Desconocido | >20             | >40             | >50            |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar formulario de feedback
- Configurar recolección de ratings
- Crear dashboard básico
- Objetivo: >3.0/5 average rating

**Fase 3 (Mes 3-4):**
- Añadir feedback contextual (por query)
- Implementar análisis de sentimiento
- Crear reports de feedback
- Objetivo: >4.0/5 average rating

**Fase 5 (Mes 7-8):**
- Implementar feedback loop
- Añadir seguimiento de issues
- Crear sistema de tickets
- Objetivo: >4.5/5 average rating

#### Métricas de Éxito

- Dashboard de feedback en Vercel
- Reports diarios/semanales
- Alertas de baja satisfacción
- Integración con sistema de tickets

### 2.3 Search Quality

#### Definición
Calidad de los resultados de búsqueda: relevancia, precisión, recall.

#### Método de Medición

```typescript
// chatbot/src/lib/rag/search-quality.ts
export class SearchQualityMetrics {
  async measureRelevance(results: SearchResult[], query: string): Promise<number> {
    // 1. Calcular relevancia promedio
    const relevanceScores = results.map(result => {
      // Usar LLM para evaluar relevancia
      return this.evaluateRelevanceWithLLM(query, result);
    });

    const avgRelevance = relevanceScores.reduce((a, b) => a + b, 0) / relevanceScores.length;
    return avgRelevance;
  }

  async measurePrecision(results: SearchResult[], relevantIds: string[]): Promise<number> {
    const relevantCount = results.filter(r => relevantIds.includes(r.id)).length;
    return relevantCount / results.length;
  }

  async measureRecall(relevantIds: string[], totalRelevant: number): Promise<number> {
    return relevantIds.length / totalRelevant;
  }

  private async evaluateRelevanceWithLLM(query: string, result: SearchResult): Promise<number> {
    const prompt = `
      Query: "${query}"
      Result: "${result.title}"
      
      Evalúa la relevancia del resultado para el query en una escala de 0 a 1.
      Devuelve SOLO el número.
    `;

    const { text } = await generateText({
      model: openai('google/gemini-flash-1.5'),
      prompt,
      temperature: 0.1,
    });

    const score = parseFloat(text.trim());
    return Math.max(0, Math.min(1, score));
  }
}
```

#### Objetivos

| Métrica               | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| --------------------- | ----------- | --------------- | --------------- | -------------- |
| **Average Relevance** | ~70%        | >75%            | >80%            | >90%           |
| **Precision @10**     | Desconocido | >70%            | >80%            | >85%           |
| **Recall @10**        | Desconocido | >60%            | >70%            | >80%           |
| **F1 Score @10**      | Desconocido | >0.65           | >0.75           | >0.85          |
| **Zero Results Rate** | ~10%        | <8%             | <5%             | <3%            |
| **User Click Rate**   | Desconocido | >20%            | >30%            | >40%           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar métricas de calidad
- Crear dataset de evaluación
- Configurar medición automática
- Objetivo: >75% average relevance

**Fase 3 (Mes 3-4):**
- Implementar hybrid search
- Añadir reranking con LLM
- Optimizar embeddings
- Objetivo: >80% average relevance

**Fase 5 (Mes 7-8):**
- Implementar feedback loop
- Añadir aprendizaje activo
- Optimizar algoritmos
- Objetivo: >90% average relevance

#### Métricas de Éxito

- Dashboard de calidad de búsqueda
- Reports diarios/semanales
- Alertas de degradación
- Integración con CI/CD

---

## 3. Métricas de Costos

### 3.1 LLM Costs

#### Definición
Costos mensuales de LLMs por proveedor y modelo.

#### Método de Medición

```python
# python-cli/cost_tracker.py
from typing import Dict
import os
from datetime import datetime, timedelta

class CostTracker:
    def __init__(self):
        self.costs: Dict[str, float] = {}

    def track_llm_call(self, model: str, input_tokens: int, output_tokens: int):
        """Track LLM call and calculate cost"""
        cost_per_1k = self.get_cost_per_1k(model)
        total_tokens = input_tokens + output_tokens
        cost = (total_tokens / 1000) * cost_per_1k

        if model not in self.costs:
            self.costs[model] = 0
        self.costs[model] += cost

    def get_cost_per_1k(self, model: str) -> float:
        """Get cost per 1K tokens for model"""
        costs = {
            'z-ai/glm-4.5-air:free': 0.0,
            'google/gemini-2.5-flash-lite': 0.000075,
            'google/gemini-3-flash-preview': 0.0003,
            'google/gemini-flash-1.5': 0.000075,
            'anthropic/claude-3.5-sonnet': 0.003,
        }
        return costs.get(model, 0.0)

    def get_monthly_cost(self) -> float:
        """Get total monthly cost"""
        return sum(self.costs.values())

    def get_cost_per_query(self, total_queries: int) -> float:
        """Get average cost per query"""
        return self.get_monthly_cost() / total_queries if total_queries > 0 else 0

    def generate_report(self) -> Dict:
        """Generate cost report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_cost': self.get_monthly_cost(),
            'by_model': self.costs,
            'cost_per_query': self.get_cost_per_query(1000),  # Estimado
        }
```

#### Objetivos

| Métrica                 | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ----------------------- | ----------- | --------------- | --------------- | -------------- |
| **Monthly LLM Cost**    | ~$100       | <$70            | <$40            | <$20           |
| **Cost per Query**      | ~$0.02      | <$0.01          | <$0.007         | <$0.005        |
| **Free Model Usage**    | Desconocido | >40%            | >60%            | >70%           |
| **Medium Model Usage**  | Desconocido | >50%            | >30%            | >25%           |
| **Premium Model Usage** | Desconocido | <10%            | <10%            | <5%            |
| **Annual LLM Cost**     | ~$1,200     | <$840           | <$480           | <$240          |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar cost tracker
- Configurar selección inteligente de modelos
- Implementar caché LLM
- Objetivo: <$70 monthly cost

**Fase 3 (Mes 3-4):**
- Optimizar prompts
- Implementar batch processing
- Aumentar cache hit rate
- Objetivo: <$40 monthly cost

**Fase 5 (Mes 7-8):**
- Implementar model selection avanzado
- Optimizar embeddings
- Implementar caching distribuido
- Objetivo: <$20 monthly cost

#### Métricas de Éxito

- Dashboard de costos en Vercel
- Reports diarios/semanales
- Alertas de sobre-gasto
- Integración con billing

### 3.2 Infrastructure Costs

#### Definición
Costos mensuales de infraestructura: hosting, storage, databases, etc.

#### Método de Medición

```typescript
// chatbot/src/lib/infrastructure-costs.ts
export interface InfrastructureCosts {
  vercel: number;
  cloudflareR2: number;
  qdrant: number;
  redis: number;
  supabase: number;
  github: number;
  total: number;
}

export async function getInfrastructureCosts(): Promise<InfrastructureCosts> {
  // Vercel
  const vercelCost = 30; // Estimado

  // Cloudflare R2
  const r2Cost = 5; // Estimado (100GB @ $0.015/GB)

  // Qdrant
  const qdrantCost = 0; // Self-hosted

  // Redis
  const redisCost = 0; // Self-hosted

  // Supabase
  const supabaseCost = 0; // Free tier

  // GitHub
  const githubCost = 0; // Free tier

  return {
    vercel: vercelCost,
    cloudflareR2: r2Cost,
    qdrant: qdrantCost,
    redis: redisCost,
    supabase: supabaseCost,
    github: githubCost,
    total: vercelCost + r2Cost + qdrantCost + redisCost + supabaseCost + githubCost,
  };
}
```

#### Objetivos

| Métrica                       | Actual | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ----------------------------- | ------ | --------------- | --------------- | -------------- |
| **Vercel Cost**               | ~$50   | <$40            | <$35            | <$30           |
| **Cloudflare R2 Cost**        | ~$10   | <$8             | <$6             | <$5            |
| **Qdrant Cost**               | $0     | $0              | $0              | $0             |
| **Redis Cost**                | ~$30   | <$20            | <$10            | $0             |
| **Supabase Cost**             | $0     | $0              | $0              | $0             |
| **GitHub Cost**               | $0     | $0              | $0              | $0             |
| **Total Infrastructure Cost** | ~$90   | <$68            | <$51            | <$35           |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Migrar Redis a self-hosted
- Optimizar uso de Vercel
- Configurar cache agresivo
- Objetivo: <$68 monthly cost

**Fase 3 (Mes 3-4):**
- Implementar Redis self-hosted
- Optimizar storage en R2
- Implementar CDN caching
- Objetivo: <$51 monthly cost

**Fase 5 (Mes 7-8):**
- Migrar a Redis self-hosted completo
- Optimizar bandwidth
- Implementar edge caching
- Objetivo: <$35 monthly cost

#### Métricas de Éxito

- Dashboard de costos en Vercel
- Reports mensuales
- Alertas de sobre-gasto
- Integración con billing

### 3.3 Total Cost of Ownership (TCO)

#### Definición
Costo total de propiedad incluyendo desarrollo, infraestructura, y mantenimiento.

#### Método de Medición

```typescript
// chatbot/src/lib/tco-calculator.ts
export interface TCOComponents {
  development: number;
  infrastructure: number;
  maintenance: number;
  llm: number;
  total: number;
}

export function calculateTCO(
  developmentHours: number,
  hourlyRate: number,
  monthlyInfrastructure: number,
  monthlyMaintenance: number,
  monthlyLLM: number,
  months: number
): TCOComponents {
  const development = developmentHours * hourlyRate;
  const infrastructure = monthlyInfrastructure * months;
  const maintenance = monthlyMaintenance * months;
  const llm = monthlyLLM * months;
  const total = development + infrastructure + maintenance + llm;

  return {
    development,
    infrastructure,
    maintenance,
    llm,
    total,
  };
}

// Ejemplo de uso
const tco = calculateTCO(
  1040, // 1,040 horas de desarrollo
  50,    // $50/hora
  90,    // $90/mes infraestructura actual
  20,    // $20/mes mantenimiento
  100,   // $100/mes LLM actual
  12     // 12 meses
);

console.log(tco);
// {
//   development: 52000,
//   infrastructure: 1080,
//   maintenance: 240,
//   llm: 1200,
//   total: 54520
// }
```

#### Objetivos

| Métrica                       | Actual   | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ----------------------------- | -------- | --------------- | --------------- | -------------- |
| **Development Cost**          | ~$52,000 | ~$52,000        | ~$52,000        | ~$52,000       |
| **Infrastructure Cost (12m)** | ~$1,080  | <$816           | <$612           | <$420          |
| **Maintenance Cost (12m)**    | ~$240    | <$240           | <$240           | <$240          |
| **LLM Cost (12m)**            | ~$1,200  | <$840           | <$480           | <$240          |
| **Total TCO (12m)**           | ~$54,520 | ~$53,896        | ~$53,332        | ~$52,900       |
| **Monthly TCO**               | ~$4,543  | ~$4,491         | ~$4,444         | ~$4,408        |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Optimizar infraestructura
- Reducir costos de LLM
- Implementar mantenimiento preventivo
- Objetivo: ~$4,491 monthly TCO

**Fase 3 (Mes 3-4):**
- Migrar a infraestructura más económica
- Reducir costos de mantenimiento
- Optimizar costos de LLM
- Objetivo: ~$4,444 monthly TCO

**Fase 5 (Mes 7-8):**
- Migrar a infraestructura self-hosted
- Reducir costos de LLM al mínimo
- Optimizar mantenimiento
- Objetivo: ~$4,408 monthly TCO

#### Métricas de Éxito

- Dashboard de TCO en Vercel
- Reports mensuales
- Proyecciones de costos
- Alertas de desviaciones

---

## 4. Métricas de Calidad de Datos

### 4.1 Extraction Quality

#### Definición
Precisión y completitud de la extracción de datos de boletines.

#### Método de Medición

```python
# python-cli/data_quality.py
from typing import Dict, List
import re

class DataQualityValidator:
    def __init__(self):
        self.required_fields = ['id', 'tipo', 'numero', 'titulo', 'contenido']
        self.min_content_length = 50
        self.max_content_length = 100000

    def validate_normativa(self, normativa: Dict) -> Dict[str, any]:
        """Validate a normativa and return quality metrics"""
        errors = []
        warnings = []

        # 1. Verificar campos obligatorios
        for field in self.required_fields:
            if field not in normativa or not normativa[field]:
                errors.append(f"Missing required field: {field}")

        # 2. Verificar longitud de contenido
        content = normativa.get('contenido', '')
        if len(content) < self.min_content_length:
            errors.append(f"Content too short: {len(content)} < {self.min_content_length}")
        if len(content) > self.max_content_length:
            warnings.append(f"Content too long: {len(content)} > {self.max_content_length}")

        # 3. Verificar formato de número
        numero = normativa.get('numero', '')
        if not re.match(r'\d+[/\-]?\d*', numero):
            errors.append(f"Invalid number format: {numero}")

        # 4. Verificar formato de fecha
        fecha = normativa.get('fecha', '')
        if not re.match(r'\d{2}/\d{2}/\d{4}', fecha):
            warnings.append(f"Invalid date format: {fecha}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': self._calculate_quality_score(errors, warnings),
        }

    def _calculate_quality_score(self, errors: List[str], warnings: List[str]) -> float:
        """Calculate quality score from 0 to 100"""
        error_penalty = 10 * len(errors)
        warning_penalty = 2 * len(warnings)
        score = 100 - error_penalty - warning_penalty
        return max(0, score)

    def validate_batch(self, normativas: List[Dict]) -> Dict[str, any]:
        """Validate a batch of normativas"""
        results = [self.validate_normativa(n) for n in normativas]
        
        valid_count = sum(1 for r in results if r['valid'])
        total_count = len(results)
        
        avg_score = sum(r['score'] for r in results) / total_count if total_count > 0 else 0

        return {
            'total': total_count,
            'valid': valid_count,
            'invalid': total_count - valid_count,
            'validity_rate': valid_count / total_count if total_count > 0 else 0,
            'average_score': avg_score,
            'results': results,
        }
```

#### Objetivos

| Métrica                   | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ------------------------- | ----------- | --------------- | --------------- | -------------- |
| **Extraction Accuracy**   | ~95%        | >95%            | >97%            | >99%           |
| **Data Completeness**     | ~90%        | >92%            | >95%            | >98%           |
| **Validity Rate**         | ~90%        | >92%            | >95%            | >98%           |
| **Average Quality Score** | Desconocido | >90             | >95             | >98            |
| **Missing Fields Rate**   | ~10%        | <8%             | <5%             | <2%            |
| **Duplicate Rate**        | ~5%         | <4%             | <2%             | <0.5%          |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar validación de calidad
- Crear dataset de evaluación
- Configurar validación automática
- Objetivo: >90% average quality score

**Fase 3 (Mes 3-4):**
- Mejorar extractores de tablas
- Mejorar extractores de montos
- Implementar validación avanzada
- Objetivo: >95% average quality score

**Fase 5 (Mes 7-8):**
- Implementar validación con LLM
- Añadir feedback loop de calidad
- Optimizar algoritmos de extracción
- Objetivo: >98% average quality score

#### Métricas de Éxito

- Dashboard de calidad de datos
- Reports diarios/semanales
- Alertas de degradación
- Integración con CI/CD

### 4.2 Data Freshness

#### Definición
Frescura de los datos: tiempo desde la última actualización.

#### Método de Medición

```python
# python-cli/data_freshness.py
from datetime import datetime, timedelta
from pathlib import Path
import json

class DataFreshnessTracker:
    def __init__(self, data_dir: str = 'boletines'):
        self.data_dir = Path(data_dir)

    def get_last_update(self) -> datetime:
        """Get last update timestamp"""
        stats_file = self.data_dir / '.last_update'
        
        if stats_file.exists():
            with open(stats_file) as f:
                return datetime.fromisoformat(f.read())
        
        # Si no existe, calcularlo
        return self._calculate_last_update()

    def _calculate_last_update(self) -> datetime:
        """Calculate last update from files"""
        files = list(self.data_dir.glob('*.json'))
        
        if not files:
            return datetime.min()

        # Obtener el timestamp más reciente
        timestamps = []
        for file in files:
            stat = file.stat()
            timestamps.append(stat.st_mtime)
        
        return datetime.fromtimestamp(max(timestamps))

    def get_data_age(self) -> timedelta:
        """Get data age"""
        last_update = self.get_last_update()
        now = datetime.now()
        return now - last_update

    def get_freshness_score(self) -> float:
        """Calculate freshness score from 0 to 100"""
        age = self.get_data_age()
        
        # 0-6 horas: 100
        # 6-24 horas: 80
        # 1-7 días: 60
        # 7-30 días: 40
        # >30 días: 20
        
        hours = age.total_seconds() / 3600
        
        if hours <= 6:
            return 100
        elif hours <= 24:
            return 80
        elif hours <= 168:  # 7 días
            return 60
        elif hours <= 720:  # 30 días
            return 40
        else:
            return 20

    def update_timestamp(self):
        """Update last update timestamp"""
        stats_file = self.data_dir / '.last_update'
        with open(stats_file, 'w') as f:
            f.write(datetime.now().isoformat())
```

#### Objetivos

| Métrica              | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| -------------------- | ----------- | --------------- | --------------- | -------------- |
| **Data Freshness**   | <24h        | <12h            | <6h             | <1h            |
| **Freshness Score**  | Desconocido | >60             | >80             | >95            |
| **Update Frequency** | Manual      | Semanal         | Diaria          | Cada 6h        |
| **Staleness Alerts** | No          | >48h            | >24h            | >6h            |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar tracking de frescura
- Configurar actualización semanal
- Implementar alertas de datos obsoletos
- Objetivo: <12h data freshness

**Fase 3 (Mes 3-4):**
- Implementar actualización diaria
- Configurar actualización automática
- Implementar dashboard de frescura
- Objetivo: <6h data freshness

**Fase 5 (Mes 7-8):**
- Implementar actualización cada 6h
- Implementar actualización incremental
- Optimizar tiempo de actualización
- Objetivo: <1h data freshness

#### Métricas de Éxito

- Dashboard de frescura de datos
- Alertas de datos obsoletos
- Reports de actualización
- Integración con CI/CD

---

## 5. Métricas de Equipo

### 5.1 Velocity & Efficiency

#### Definición
Velocidad del equipo: story points completados por sprint, lead time, cycle time.

#### Método de Medición

```typescript
// chatbot/src/lib/team-metrics.ts
export interface TeamMetrics {
  velocity: number;          // Story points per sprint
  leadTime: number;          // Time from start to merge
  cycleTime: number;         // Time from PR to merge
  codeReviewTime: number;     // Time from PR to review completion
  bugFixTime: number;        // Time from bug report to fix
  teamSatisfaction: number;   // Team satisfaction score
}

export async function getTeamMetrics(): Promise<TeamMetrics> {
  // Obtener métricas de GitHub
  // Obtener métricas de Jira/Linear
  // Obtener métricas de surveys
  
  return {
    velocity: 25,
    leadTime: 3,  // días
    cycleTime: 1,  // días
    codeReviewTime: 0.5,  // días
    bugFixTime: 2,  // días
    teamSatisfaction: 4.2,  // /5
  };
}
```

#### Objetivos

| Métrica                            | Actual      | Objetivo Fase 1 | Objetivo Fase 3 | Objetivo Final |
| ---------------------------------- | ----------- | --------------- | --------------- | -------------- |
| **Velocity (story points/sprint)** | Desconocido | >15             | >20             | >25            |
| **Lead Time (días)**               | Desconocido | <5              | <3              | <2             |
| **Cycle Time (días)**              | Desconocido | <3              | <2              | <1             |
| **Code Review Time (horas)**       | Desconocido | <24             | <12             | <8             |
| **Bug Fix Time (horas)**           | Desconocido | <48             | <24             | <16            |
| **Team Satisfaction**              | Desconocido | >3.5/5          | >4.0/5          | >4.5/5         |

#### Plan de Acción

**Fase 1 (Mes 1-2):**
- Implementar tracking de story points
- Configurar métricas de GitHub
- Implementar surveys de satisfacción
- Objetivo: >15 velocity

**Fase 3 (Mes 3-4):**
- Optimizar proceso de code review
- Implementar pair programming
- Añadir mentoría
- Objetivo: >20 velocity

**Fase 5 (Mes 7-8):**
- Implementar CI/CD automatizado
- Optimizar proceso de testing
- Implementar automación de tareas
- Objetivo: >25 velocity

#### Métricas de Éxito

- Dashboard de métricas de equipo
- Reports de sprint
- Alertas de degradación
- Integración con GitHub/Jira

---

## 6. Dashboard Consolidado

### 6.1 Dashboard Principal

```typescript
// chatbot/src/app/api/metrics/route.ts
import { NextResponse } from 'next/server';
import { metrics } from '@/lib/metrics';
import { teamMetrics } from '@/lib/team-metrics';

export async function GET() {
  const [
    technicalMetrics,
    productMetrics,
    costMetrics,
    dataQualityMetrics,
    teamMetrics,
  ] = await Promise.all([
    getTechnicalMetrics(),
    getProductMetrics(),
    getCostMetrics(),
    getDataQualityMetrics(),
    getTeamMetrics(),
  ]);

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    status: 'healthy',
    metrics: {
      technical: technicalMetrics,
      product: productMetrics,
      costs: costMetrics,
      dataQuality: dataQualityMetrics,
      team: teamMetrics,
    },
  });
}
```

### 6.2 Métricas Consolidadas por Categoría

```typescript
interface ConsolidatedMetrics {
  technical: {
    testCoverage: number;
    ciCdPerformance: number;
    codeQuality: number;
    performance: number;
  };
  product: {
    userEngagement: number;
    userSatisfaction: number;
    searchQuality: number;
  };
  costs: {
    llmCosts: number;
    infrastructureCosts: number;
    totalTCO: number;
  };
  dataQuality: {
    extractionQuality: number;
    dataFreshness: number;
    completeness: number;
  };
  team: {
    velocity: number;
    leadTime: number;
    cycleTime: number;
    teamSatisfaction: number;
  };
}
```

---

## 7. Plan de Monitoreo

### 7.1 Frecuencia de Monitoreo

| Métrica               | Frecuencia  | Responsable         | Alertas          |
| --------------------- | ----------- | ------------------- | ---------------- |
| **Test Coverage**     | Semanal     | QA Engineer         | <70%             |
| **CI/CD Performance** | Cada PR     | DevOps Engineer     | >10min           |
| **Code Quality**      | Cada commit | Todos               | <90/100          |
| **Performance**       | Diaria      | DevOps Engineer     | >2s API time     |
| **User Engagement**   | Diaria      | Product Manager     | <50 DAU          |
| **User Satisfaction** | Semanal     | Product Manager     | <3.5/5           |
| **Search Quality**    | Semanal     | Backend Developer   | <75% relevance   |
| **LLM Costs**         | Mensual     | DevOps Engineer     | >$100            |
| **Data Quality**      | Diaria      | Data Engineer       | <90% validity    |
| **Team Velocity**     | Cada sprint | Engineering Manager | <15 story points |

### 7.2 Alertas Automáticas

```typescript
// chatbot/src/lib/alerts.ts
export class AlertManager {
  private webhookUrl: string;
  private alertThresholds = {
    testCoverage: 70,      // <70% trigger alert
    ciCdTime: 600,        // >10min trigger alert
    apiLatency: 2000,     // >2s trigger alert
    userSatisfaction: 3.5, // <3.5/5 trigger alert
    searchQuality: 75,     // <75% trigger alert
    monthlyCost: 100,      // >$100 trigger alert
    dataQuality: 90,      // <90% trigger alert
    teamVelocity: 15,     // <15 story points trigger alert
  };

  async checkAlerts(metrics: ConsolidatedMetrics) {
    const alerts = [];

    // Technical alerts
    if (metrics.technical.testCoverage < this.alertThresholds.testCoverage) {
      alerts.push({
        level: 'warning',
        message: `Test coverage below threshold: ${metrics.technical.testCoverage}%`,
      });
    }

    if (metrics.technical.ciCdPerformance > this.alertThresholds.ciCdTime) {
      alerts.push({
        level: 'warning',
        message: `CI/CD time above threshold: ${metrics.technical.ciCdPerformance}s`,
      });
    }

    // Product alerts
    if (metrics.product.userSatisfaction < this.alertThresholds.userSatisfaction) {
      alerts.push({
        level: 'error',
        message: `User satisfaction below threshold: ${metrics.product.userSatisfaction}/5`,
      });
    }

    // Cost alerts
    if (metrics.costs.llmCosts > this.alertThresholds.monthlyCost) {
      alerts.push({
        level: 'warning',
        message: `Monthly LLM cost above threshold: $${metrics.costs.llmCosts}`,
      });
    }

    // Data quality alerts
    if (metrics.dataQuality.extractionQuality < this.alertThresholds.dataQuality) {
      alerts.push({
        level: 'error',
        message: `Data quality below threshold: ${metrics.dataQuality.extractionQuality}%`,
      });
    }

    // Team alerts
    if (metrics.team.velocity < this.alertThresholds.teamVelocity) {
      alerts.push({
        level: 'warning',
        message: `Team velocity below threshold: ${metrics.team.velocity} story points`,
      });
    }

    // Enviar alertas
    for (const alert of alerts) {
      await this.sendAlert(alert);
    }
  }

  private async sendAlert(alert: any) {
    await fetch(this.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level: alert.level,
        message: alert.message,
        timestamp: new Date().toISOString(),
      }),
    });
  }
}
```

---

## 8. Conclusiones

### 8.1 Resumen Ejecutivo

Este documento define **métricas de éxito específicas y accionables** para medir el progreso y el impacto de las mejoras propuestas. Cada métrica incluye:

1. **Definición clara:** Qué se mide y por qué
2. **Método de medición:** Cómo se mide técnicamente
3. **Objetivos por fase:** Metas claras y alcanzables
4. **Plan de acción:** Pasos concretos para lograr los objetivos
5. **Métricas de éxito:** Indicadores de logro

### 8.2 Principios Clave

1. **SMART:** Todas las métricas son Específicas, Medibles, Alcanzables, Relevantes, Temporales
2. **Priorizadas:** Enfocadas en impacto de negocio y valor para el usuario
3. **Accionables:** Cada métrica tiene un plan de acción claro
4. **Rastreables:** Todas las métricas pueden ser monitoreadas automáticamente
5. **Transparentes:** Dashboard consolidado para visibilidad completa

### 8.3 Próximos Pasos

1. **Implementar Dashboard de Métricas**
   - Crear endpoint `/api/metrics`
   - Implementar recolección automática de datos
   - Configurar visualización en Vercel

2. **Configurar Alertas Automáticas**
   - Implementar AlertManager
   - Configurar webhooks (Slack/Discord)
   - Definir thresholds y frecuencia

3. **Establecer Reviews Regulares**
   - Revisión semanal de métricas
   - Ajustar objetivos según progreso
   - Documentar lecciones aprendidas

4. **Optimizar Continuamente**
   - Ajustar métricas según necesidades
   - Añadir nuevas métricas según requerimientos
   - Eliminar métricas que no aportan valor

---

**Fin del Documento**
