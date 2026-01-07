# Plan de Implementación - SIBOM Scraper Assistant

## Información del Proyecto

**Nombre:** SIBOM Scraper Assistant  
**Versión:** 2.0 (Migración OpenRouter + Optimizaciones)  
**Fecha:** 2026-01-07  
**Estado:** Plan de implementación basado en requirements y design  
**Tipo:** Sistema completo de scraping web + chatbot conversacional  

## Resumen Ejecutivo

Este documento define el plan de implementación detallado para el SIBOM Scraper Assistant, organizando las tareas en sprints ejecutables con prioridades claras. La mayoría de la funcionalidad ya está implementada, por lo que este plan se enfoca en mejoras de calidad, testing automatizado y optimizaciones pendientes.

## Metodología de Implementación

### Principios de Desarrollo
1. **Incremental**: Mejoras pequeñas y frecuentes
2. **Testing-First**: Cada feature debe tener tests antes de deployment
3. **Performance-Aware**: Métricas de performance en cada cambio
4. **User-Centric**: Priorizar mejoras que impacten la experiencia del usuario

### Estructura de Sprints
- **Sprint 1**: Testing y Calidad (2 semanas)
- **Sprint 2**: Optimizaciones de Performance (1 semana)  
- **Sprint 3**: Métricas y Monitoreo (1 semana)
- **Sprint 4**: Mejoras de UX y Accesibilidad (1 semana)

## Sprint 1: Testing y Calidad (2 semanas)

### Objetivo
Implementar testing automatizado completo y mejorar la calidad del código existente.

### Tareas Principales

#### T1.1: Configuración de Testing Framework
**Prioridad:** Alta  
**Estimación:** 4 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Configurar Vitest como framework de testing principal para el frontend Next.js.

**Criterios de Aceptación:**
- Vitest configurado con soporte para React Testing Library
- Setup de mocks para Next.js (router, fetch, localStorage)
- Configuración de coverage reporting (texto + HTML)
- Scripts npm para testing (`test`, `test:watch`, `test:coverage`)

**Archivos a Crear/Modificar:**
```
chatbot/vitest.config.ts
chatbot/src/test/setup.ts
chatbot/package.json (scripts)
```

**Implementación:**
```typescript
// chatbot/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/app/layout.tsx',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### T1.2: Unit Tests para Query Classifier*
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar tests unitarios completos para el sistema de clasificación de consultas.

**Criterios de Aceptación:**
- Tests para `needsRAGSearch()` con casos edge
- Tests para `isFAQQuestion()` con diferentes patrones
- Tests para `calculateOptimalLimit()` con filtros
- Tests para `getOffTopicResponse()` con categorización
- Coverage > 90% para query-classifier.ts

**Archivos a Crear:**
```
chatbot/src/lib/__tests__/query-classifier.test.ts
```

**Casos de Test Críticos:**
```typescript
describe('needsRAGSearch', () => {
  it('should return true for ordinance-related queries', () => {
    const queries = [
      'ordenanza de tránsito',
      'decreto municipal',
      'normativa vigente'
    ];
    queries.forEach(query => {
      expect(needsRAGSearch(query)).toBe(true);
    });
  });

  it('should return false for greetings', () => {
    const greetings = ['hola', 'buenos días', 'cómo estás'];
    greetings.forEach(greeting => {
      expect(needsRAGSearch(greeting)).toBe(false);
    });
  });
});
```

#### T1.3: Unit Tests para Filter Extractor*
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar tests unitarios para el sistema de extracción automática de filtros.

**Criterios de Aceptación:**
- Tests para `extractYear()` con años válidos/inválidos
- Tests para `extractMunicipality()` case-insensitive
- Tests para `extractOrdinanceType()` con diferentes patrones
- Tests para `extractFiltersFromQuery()` con consultas complejas
- Coverage > 90% para query-filter-extractor.ts

**Archivos a Crear:**
```
chatbot/src/lib/__tests__/query-filter-extractor.test.ts
```

#### T1.4: Unit Tests para BM25 Algorithm*
**Prioridad:** Alta  
**Estimación:** 8 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar tests unitarios y de performance para el algoritmo BM25.

**Criterios de Aceptación:**
- Tests para `tokenize()` con texto español y caracteres especiales
- Tests para `BM25Index` con ranking por relevancia
- Tests para `explainScore()` con debugging de scores
- Performance tests con 1000+ documentos
- Memory usage tests para prevenir leaks

**Archivos a Crear:**
```
chatbot/src/lib/rag/__tests__/bm25.test.ts
chatbot/src/lib/rag/__tests__/bm25-performance.test.ts
```

#### T1.5: Component Tests para ActiveFilters*
**Prioridad:** Media  
**Estimación:** 6 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar tests de componentes React para el sistema de filtros.

**Criterios de Aceptación:**
- Tests para renderizado de badges de filtros
- Tests para interacciones de usuario (click, remove)
- Tests para formateo inteligente de fechas
- Tests para sincronización con estado global
- Tests de accesibilidad básica

**Archivos a Crear:**
```
chatbot/src/components/chat/__tests__/ActiveFilters.test.tsx
```

#### T1.6: API Route Tests*
**Prioridad:** Media  
**Estimación:** 8 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Implementar tests de integración para el endpoint principal de chat.

**Criterios de Aceptación:**
- Tests para requests válidos con streaming
- Tests para manejo de errores (API key, rate limits)
- Tests para consultas off-topic sin LLM
- Tests para clasificación automática de consultas
- Mocking completo de OpenRouter

**Archivos a Crear:**
```
chatbot/src/app/api/chat/__tests__/route.test.ts
```

#### T1.7: Integration Tests para Chat Flow*
**Prioridad:** Media  
**Estimación:** 10 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Implementar tests de integración end-to-end para el flujo completo de chat.

**Criterios de Aceptación:**
- Tests para interacción completa usuario-chat
- Tests para aplicación y remoción de filtros
- Tests para estados de loading y error
- Tests para persistencia de historial
- Tests de responsive design básico

**Archivos a Crear:**
```
chatbot/src/__tests__/integration/chat-flow.test.ts
```

### Tareas de Soporte

#### T1.8: Python Testing Setup*
**Prioridad:** Baja  
**Estimación:** 4 horas  
**Responsable:** Backend Developer  

**Descripción:**
Configurar pytest para el backend Python con tests básicos.

**Criterios de Aceptación:**
- pytest configurado con coverage
- Tests básicos para SIBOMScraper class
- Mocking de OpenRouter API calls
- Tests para rate limiting y retry logic

**Archivos a Crear:**
```
python-cli/tests/test_scraper.py
python-cli/pytest.ini
python-cli/requirements-dev.txt
```

#### T1.9: Error Scenario Testing*
**Prioridad:** Media  
**Estimación:** 6 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Implementar tests específicos para escenarios de error y recovery.

**Criterios de Aceptación:**
- Tests para fallbacks de RAG (cache antiguo, respuesta emergencia)
- Tests para manejo de JSON malformado
- Tests para timeout de requests
- Tests para degradación graceful

## Sprint 2: Optimizaciones de Performance (1 semana)

### Objetivo
Implementar las optimizaciones de performance pendientes identificadas en el design.

### Tareas Principales

#### T2.1: Tree-shaking de Lucide React
**Prioridad:** Alta  
**Estimación:** 2 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Optimizar imports de iconos para reducir bundle size significativamente.

**Criterios de Aceptación:**
- Importar solo iconos específicos usados
- Reducción de bundle size de ~450KB
- Verificar que todos los iconos siguen funcionando
- Actualizar imports en todos los componentes

**Archivos a Modificar:**
```
chatbot/src/components/**/*.tsx (todos los que usan iconos)
```

**Implementación:**
```typescript
// Antes
import { Search, Filter, X } from 'lucide-react';

// Después  
import Search from 'lucide-react/dist/esm/icons/search';
import Filter from 'lucide-react/dist/esm/icons/filter';
import X from 'lucide-react/dist/esm/icons/x';
```

#### T2.2: Code Splitting por Rutas
**Prioridad:** Media  
**Estimación:** 3 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar lazy loading de componentes pesados para reducir bundle inicial.

**Criterios de Aceptación:**
- Lazy loading de ReactMarkdown y componentes pesados
- Reducción del bundle inicial
- Loading states apropiados durante carga
- No impacto negativo en UX

**Implementación:**
```typescript
// Lazy loading de componentes pesados
const ReactMarkdown = lazy(() => import('react-markdown'));
const AdvancedFilters = lazy(() => import('./AdvancedFilters'));

// Con Suspense
<Suspense fallback={<div>Cargando...</div>}>
  <ReactMarkdown>{content}</ReactMarkdown>
</Suspense>
```

#### T2.3: Image Optimization
**Prioridad:** Baja  
**Estimación:** 1 hora  
**Responsable:** Frontend Developer  

**Descripción:**
Optimizar imágenes usando Next.js Image component.

**Criterios de Aceptación:**
- Reemplazar tags `<img>` con `<Image>` de Next.js
- Configurar formatos WebP con fallbacks
- Lazy loading automático de imágenes
- Responsive images para diferentes tamaños

#### T2.4: Service Worker para Cache*
**Prioridad:** Baja  
**Estimación:** 4 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar service worker para cache de assets estáticos y funcionalidad offline básica.

**Criterios de Aceptación:**
- Cache de assets estáticos (JS, CSS, fonts)
- Cache de respuestas de API por tiempo limitado
- Funcionalidad offline básica para consultas recientes
- Estrategia de cache-first para assets, network-first para API

### Tareas de Medición

#### T2.5: Performance Benchmarking
**Prioridad:** Alta  
**Estimación:** 2 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar benchmarks automáticos para medir mejoras de performance.

**Criterios de Aceptación:**
- Lighthouse CI configurado
- Métricas de Web Vitals automáticas
- Bundle analyzer en CI/CD
- Comparación before/after de optimizaciones

**Archivos a Crear:**
```
chatbot/.github/workflows/performance.yml
chatbot/scripts/analyze-bundle.js
```

## Sprint 3: Métricas y Monitoreo (1 semana)

### Objetivo
Implementar sistema completo de métricas, analytics y monitoreo.

### Tareas Principales

#### T3.1: Sistema de Métricas Básico
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Implementar tracking básico de métricas de uso y performance.

**Criterios de Aceptación:**
- Endpoint `/api/metrics` con estadísticas del sistema
- Tracking de queries por día, usuarios únicos
- Métricas de performance (tiempo respuesta, cache hit rate)
- Métricas de costos (tokens usados, costo estimado)

**Archivos a Crear:**
```
chatbot/src/app/api/metrics/route.ts
chatbot/src/lib/metrics/collector.ts
chatbot/src/lib/metrics/types.ts
```

**Implementación:**
```typescript
interface SystemMetrics {
  performance: {
    avgResponseTime: number;
    cacheHitRate: number;
    errorRate: number;
  };
  usage: {
    queriesPerDay: number;
    uniqueUsers: number;
    popularMunicipalities: string[];
  };
  costs: {
    dailyTokens: number;
    estimatedDailyCost: number;
  };
}
```

#### T3.2: Dashboard de Métricas
**Prioridad:** Media  
**Estimación:** 8 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Crear dashboard interno para visualizar métricas del sistema.

**Criterios de Aceptación:**
- Página `/admin/metrics` con gráficos básicos
- Visualización de métricas en tiempo real
- Filtros por fecha y municipio
- Exportación de datos en CSV/JSON

**Archivos a Crear:**
```
chatbot/src/app/admin/metrics/page.tsx
chatbot/src/components/admin/MetricsDashboard.tsx
chatbot/src/components/admin/MetricsChart.tsx
```

#### T3.3: Health Checks Automáticos
**Prioridad:** Alta  
**Estimación:** 4 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Implementar health checks para monitorear estado del sistema.

**Criterios de Aceptación:**
- Endpoint `/api/health` con status de componentes
- Verificación de conectividad a OpenRouter
- Verificación de disponibilidad de datos
- Alertas básicas por email/webhook

**Archivos a Crear:**
```
chatbot/src/app/api/health/route.ts
chatbot/src/lib/health/checker.ts
```

#### T3.4: Error Tracking Mejorado
**Prioridad:** Media  
**Estimación:** 4 horas  
**Responsable:** Full-stack Developer  

**Descripción:**
Mejorar el sistema de tracking y categorización de errores.

**Criterios de Aceptación:**
- Categorización automática de errores
- Tracking de error rates por tipo
- Alertas para error rates elevados
- Dashboard de errores con trends

### Tareas de Integración

#### T3.5: Analytics de Usuario*
**Prioridad:** Baja  
**Estimación:** 6 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar analytics básicos de comportamiento de usuario (privacy-first).

**Criterios de Aceptación:**
- Tracking de eventos sin PII
- Análisis de patrones de consulta
- Métricas de engagement y retención
- Cumplimiento con GDPR/privacy

## Sprint 4: Mejoras de UX y Accesibilidad (1 semana)

### Objetivo
Mejorar la experiencia de usuario y accesibilidad del sistema.

### Tareas Principales

#### T4.1: Mejoras de Accesibilidad
**Prioridad:** Alta  
**Estimación:** 6 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar mejoras de accesibilidad siguiendo WCAG 2.1 AA.

**Criterios de Aceptación:**
- Navegación completa por teclado
- Screen reader support mejorado
- Contraste de colores WCAG AA compliant
- ARIA labels y roles apropiados
- Focus management en modales y filtros

**Archivos a Modificar:**
```
chatbot/src/components/**/*.tsx (todos los componentes UI)
chatbot/src/styles/globals.css (contraste de colores)
```

#### T4.2: Virtual Scrolling para Mensajes*
**Prioridad:** Media  
**Estimación:** 8 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Implementar virtual scrolling para conversaciones muy largas.

**Criterios de Aceptación:**
- Renderizado eficiente de 100+ mensajes
- Scroll suave y natural
- Preservar posición al agregar mensajes
- Performance mejorada en conversaciones largas

#### T4.3: Mejoras de Mobile UX
**Prioridad:** Alta  
**Estimación:** 4 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Optimizar la experiencia móvil del chat.

**Criterios de Aceptación:**
- Teclado virtual no oculta input
- Filtros optimizados para touch
- Swipe gestures para navegación
- Performance optimizada en dispositivos lentos

#### T4.4: Estados de Loading Mejorados
**Prioridad:** Media  
**Estimación:** 3 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Mejorar feedback visual durante operaciones asíncronas.

**Criterios de Aceptación:**
- Skeleton loading para mensajes
- Progress indicators para operaciones largas
- Estados de error más informativos
- Animaciones suaves y no intrusivas

### Tareas de Pulido

#### T4.5: Optimización de Animaciones
**Prioridad:** Baja  
**Estimación:** 2 horas  
**Responsable:** Frontend Developer  

**Descripción:**
Optimizar animaciones para mejor performance y UX.

**Criterios de Aceptación:**
- Animaciones respetan `prefers-reduced-motion`
- 60fps en animaciones críticas
- Transiciones suaves entre estados
- No animaciones innecesarias que distraigan

## Tareas de Mantenimiento Continuo

### M1: Actualización de Dependencias
**Frecuencia:** Mensual  
**Estimación:** 2 horas/mes  
**Responsable:** Full-stack Developer  

**Descripción:**
Mantener dependencias actualizadas y seguras.

**Criterios de Aceptación:**
- Dependencias críticas siempre actualizadas
- Tests pasan después de actualizaciones
- Security vulnerabilities resueltas < 48h
- Breaking changes documentados

### M2: Monitoreo de Costos LLM
**Frecuencia:** Semanal  
**Estimación:** 1 hora/semana  
**Responsable:** Product Owner  

**Descripción:**
Monitorear y optimizar costos de uso de LLM.

**Criterios de Aceptación:**
- Tracking semanal de costos por modelo
- Alertas si costos exceden presupuesto
- Análisis de eficiencia de clasificación de consultas
- Optimizaciones basadas en patrones de uso

### M3: Backup y Recovery
**Frecuencia:** Diaria (automática)  
**Estimación:** Setup inicial 4 horas  
**Responsable:** DevOps/Full-stack Developer  

**Descripción:**
Implementar backup automático de datos críticos.

**Criterios de Aceptación:**
- Backup diario de archivos JSON
- Versionado de datos con Git
- Procedimiento de recovery documentado
- Tests de recovery trimestrales

## Criterios de Definición de Terminado

### Para Todas las Tareas
- [ ] Código implementado y funcionando
- [ ] Tests unitarios/integración pasando (si aplica)
- [ ] Documentación actualizada
- [ ] Code review completado
- [ ] Performance impact medido
- [ ] Deployed a staging y validado

### Para Tareas de Testing (marcadas con *)
- [ ] Coverage > 80% para código nuevo
- [ ] Tests incluyen casos edge y error scenarios
- [ ] Tests son determinísticos y no flaky
- [ ] Documentación de casos de test críticos

### Para Tareas de Performance
- [ ] Métricas before/after documentadas
- [ ] Lighthouse score mejorado
- [ ] Bundle size reducido (si aplica)
- [ ] No regresiones en funcionalidad

### Para Tareas de UX
- [ ] Validado en múltiples dispositivos
- [ ] Accesibilidad básica verificada
- [ ] Feedback de usuario incorporado
- [ ] Responsive design funcionando

## Riesgos y Mitigaciones

### Riesgo 1: Testing Overhead
**Probabilidad:** Media  
**Impacto:** Medio  
**Mitigación:** Priorizar tests de componentes críticos, usar property-based testing para casos complejos

### Riesgo 2: Performance Regressions
**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:** Benchmarks automáticos en CI/CD, rollback plan definido

### Riesgo 3: Costos LLM Inesperados
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:** Alertas de costo, rate limiting agresivo, fallbacks sin LLM

### Riesgo 4: Complejidad de Mantenimiento
**Probabilidad:** Media  
**Impacto:** Medio  
**Mitigación:** Documentación exhaustiva, code reviews estrictos, refactoring incremental

## Métricas de Éxito

### Sprint 1 (Testing)
- [ ] Coverage de código > 80%
- [ ] 0 tests flaky en CI/CD
- [ ] Tiempo de CI/CD < 10 minutos
- [ ] Bugs detectados por tests > bugs en producción

### Sprint 2 (Performance)
- [ ] Bundle size reducido > 30%
- [ ] Lighthouse Performance Score > 90
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s

### Sprint 3 (Métricas)
- [ ] Dashboard de métricas funcional
- [ ] Health checks automáticos implementados
- [ ] Error rate < 1%
- [ ] Alertas funcionando correctamente

### Sprint 4 (UX)
- [ ] WCAG 2.1 AA compliance > 95%
- [ ] Mobile usability score > 90
- [ ] User satisfaction > 4.5/5
- [ ] Task completion rate > 95%

## Conclusión

Este plan de implementación prioriza la calidad y estabilidad del sistema existente, agregando las capas de testing, monitoreo y optimización necesarias para un producto de nivel producción. La estructura en sprints permite entregas incrementales de valor mientras se mantiene el sistema funcionando.

Las tareas marcadas con asterisco (*) son opcionales y pueden ser diferidas si los recursos son limitados, pero se recomienda completarlas para garantizar la calidad a largo plazo del sistema.

---

**Última actualización:** 2026-01-07  
**Estado:** Plan de implementación listo para ejecución  
**Próximo paso:** Iniciar Sprint 1 con configuración de testing framework