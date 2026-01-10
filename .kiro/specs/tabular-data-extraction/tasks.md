# Plan de Implementación: Extracción de Datos Tabulares

## Resumen

Implementar extracción estructurada de tablas HTML en el scraper SIBOM, preservando la semántica columna-fila para queries computacionales en el sistema RAG.

## Tareas

- [x] 1. Crear módulo TableExtractor en Python
  - [x] 1.1 Crear archivo `python-cli/table_extractor.py` con clases base
    - Definir dataclasses: `TableSchema`, `TableStats`, `StructuredTable`
    - Crear clase `TableExtractor` con constructor
    - _Requisitos: 2.1, 2.2, 3.5_

  - [x] 1.2 Implementar detección de tablas HTML
    - Método `_detect_tables()` que encuentra elementos `<table>` válidos
    - Filtrar tablas con menos de 2 filas o 2 columnas
    - Manejar tablas anidadas (procesar solo la más interna)
    - _Requisitos: 1.1, 1.3, 1.4_

  - [x] 1.3 Implementar extracción de contexto circundante
    - Método `_extract_context()` que obtiene texto antes/después de la tabla
    - Limitar a 500 caracteres máximo cada lado
    - _Requisitos: 1.2_

  - [x] 1.4 Escribir tests unitarios para detección de tablas
    - Test tabla válida (≥2 filas, ≥2 columnas)
    - Test tabla inválida (ignorar)
    - Test tablas anidadas
    - _Requisitos: 1.1, 1.3, 1.4_

- [x] 2. Implementar extracción de estructura tabular
  - [x] 2.1 Implementar extracción de headers
    - Método `_extract_headers()` que identifica primera fila como headers
    - Método `_normalize_header()` que convierte a snake_case
    - Manejar caracteres especiales (Nº, $, %, etc.)
    - _Requisitos: 2.1, 2.6_

  - [x] 2.2 Implementar parseo de valores numéricos
    - Método `_parse_numeric()` que detecta y convierte números
    - Soportar formato argentino: "1.500,00" → 1500.00
    - Soportar formato simple: "1500" → 1500
    - Retornar string si no es número válido
    - _Requisitos: 2.3, 2.4_

  - [x] 2.3 Implementar extracción de filas de datos
    - Método `_extract_rows()` que crea array de dicts
    - Cada dict tiene keys = headers normalizados
    - Valores tipados (número o string)
    - Celdas vacías como None
    - _Requisitos: 2.2, 2.5_

  - [x] 2.4 Escribir property test para parseo numérico argentino
    - **Property 3: Parseo Numérico (Formato Argentino)**
    - Generar números aleatorios, formatear como argentino, parsear y verificar
    - _Requisitos: 2.3, 2.4_

- [x] 3. Implementar generación de metadatos
  - [x] 3.1 Implementar inferencia de tipos de columnas
    - Método `_infer_types()` que analiza datos y determina tipo
    - Tipos: "string", "number", "date"
    - _Requisitos: 3.5_

  - [x] 3.2 Implementar cálculo de estadísticas
    - Método `_calculate_stats()` para columnas numéricas
    - Calcular: sum, max, min, avg, count
    - _Requisitos: 3.3_

  - [x] 3.3 Implementar generación de Markdown
    - Método `_generate_markdown()` que crea tabla Markdown válida
    - Formatear números con separador de miles para legibilidad
    - _Requisitos: 3.4_

  - [x] 3.4 Implementar generación de título y descripción
    - Método `_generate_title()` basado en contexto y headers
    - Descripción simple basada en columnas y cantidad de filas
    - _Requisitos: 3.1, 3.2_

  - [x] 3.5 Escribir property test para estadísticas
    - **Property 4: Correctitud de Estadísticas**
    - Generar arrays de números, calcular stats, verificar matemáticamente
    - _Requisitos: 3.3_

- [x] 4. Checkpoint - Verificar módulo TableExtractor
  - ✅ Ejecutar todos los tests, verificar que pasen (33/33 passed)
  - Preguntar al usuario si hay dudas

- [x] 5. Integrar con SIBOMScraper
  - [x] 5.1 Crear método `parse_final_content_structured()`
    - Nuevo método en `SIBOMScraper` que usa `TableExtractor`
    - Retorna dict con `text_content`, `tables`, `metadata`
    - _Requisitos: 4.1, 4.4_

  - [x] 5.2 Implementar reemplazo de tablas por placeholders
    - Reemplazar cada `<table>` con `[TABLA_N]` en el texto
    - Registrar posición del placeholder
    - _Requisitos: 4.2, 4.3_

  - [x] 5.3 Actualizar método `process_bulletin()` para usar nuevo formato
    - Llamar a `parse_final_content_structured()` en lugar de `parse_final_content()`
    - Mantener campo `fullText` para compatibilidad (deprecated)
    - Agregar nuevos campos al JSON de salida
    - _Requisitos: 4.5_

  - [x] 5.4 Escribir property test para round-trip JSON
    - **Property 7: Integridad Round-Trip JSON**
    - Serializar tabla, deserializar, verificar equivalencia
    - _Requisitos: 5.1, 5.2, 5.3_

- [x] 6. Implementar manejo de errores robusto
  - [x] 6.1 Agregar try-catch en extracción de cada tabla
    - Capturar errores por tabla individual
    - Registrar en `extraction_errors`
    - Continuar con siguiente tabla
    - _Requisitos: 7.1, 7.4_

  - [x] 6.2 Implementar fallbacks para casos edge
    - Tabla malformada → warning + texto plano
    - Conversión numérica fallida → mantener como string
    - Contexto no disponible → título por defecto
    - _Requisitos: 7.2, 7.3_

  - [x] 6.3 Escribir tests para casos de error
    - Test tabla malformada
    - Test valor numérico inválido
    - Test sin contexto
    - _Requisitos: 7.1, 7.2, 7.3_

- [x] 7. Checkpoint - Verificar integración con scraper
  - Ejecutar scraper en un boletín de prueba
  - Verificar JSON de salida tiene estructura correcta
  - ✅ Usuario confirmó ejecución exitosa

- [x] 8. Actualizar sistema RAG (TypeScript)
  - [x] 8.1 Agregar detección de queries computacionales
    - Función `isComputationalQuery()` con patrones regex
    - Patrones: suma, máximo, comparar, cuántos, etc.
    - _Requisitos: 6.1_

  - [x] 8.2 Actualizar tipos TypeScript
    - Interfaces `TableSchema`, `TableStats`, `StructuredTable`
    - Actualizar interface `Document` con campo `tables`
    - _Requisitos: 6.2_

  - [x] 8.3 Crear módulo `table-formatter.ts`
    - Función `formatTableForLLM()` - formatea tabla individual
    - Función `formatTablesForLLM()` - formatea múltiples tablas
    - Función `filterRelevantTables()` - filtra por relevancia
    - Formatear tablas con Markdown + estadísticas pre-calculadas
    - _Requisitos: 6.3, 6.4_

  - [x] 8.4 Actualizar retriever para incluir datos de tablas
    - Modificar `retrieveContext()` para detectar queries computacionales
    - Cargar datos estructurados de tablas desde JSON
    - Incluir datos tabulares en contexto cuando sea necesario
    - _Requisitos: 6.2_

  - [x] 8.5 Escribir tests para Query Router y Table Formatter
    - Test queries computacionales detectadas
    - Test queries semánticas no afectadas
    - Test formateo de tablas
    - Test filtrado de tablas relevantes
    - _Requisitos: 6.1_

  - [x] 8.6 Configurar infraestructura de testing
    - Crear `vitest.config.ts`
    - Crear `src/test/setup.ts`
    - Actualizar `package.json` con scripts de testing
    - Agregar dependencias de testing

- [x] 9. Checkpoint final
  - [x] Ejecutar todos los tests (Python + TypeScript)
    - ✅ Python: 33/33 tests pasando
    - ✅ TypeScript: 38/38 tests pasando
  - [ ] Verificar que el scraper genera JSON correcto
    - ⚠️ JSON existente no tiene campo `tables` (generado con versión antigua)
    - ⏳ Usuario debe regenerar JSON con scraper actualizado
  - [ ] Verificar que el chatbot puede responder queries computacionales
    - ⏳ Pendiente: requiere JSON con tablas estructuradas
  - ✅ Todos los tests unitarios pasando
  - ✅ Implementación completa (Python + TypeScript)

## Notas

- Todos los tests son obligatorios para garantizar cobertura completa
- Cada tarea referencia los requisitos específicos que implementa
- Los checkpoints permiten validación incremental
- Property tests usan `hypothesis` (Python) para generar casos de prueba
