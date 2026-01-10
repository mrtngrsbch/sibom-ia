# Tarea 9: Checkpoint Final - Instrucciones de Validación

## Objetivo

Validar que la implementación completa de extracción de datos tabulares funciona correctamente en ambos componentes (Python scraper + TypeScript chatbot).

---

## Paso 1: Instalar Dependencias de Testing (TypeScript)

```bash
cd chatbot
npm install --save-dev vitest@^1.0.4 @vitest/ui@^1.0.4 @vitejs/plugin-react@^4.2.1 jsdom@^23.0.1 @testing-library/react@^14.1.2 @testing-library/jest-dom@^6.1.5
```

**Verificar instalación:**
```bash
npm list vitest
```

---

## Paso 2: Ejecutar Tests TypeScript

```bash
cd chatbot
npm test
```

**Salida esperada:**
```
✓ src/lib/__tests__/query-classifier.test.ts (30+ tests)
  ✓ isComputationalQuery
    ✓ should detect aggregation queries
    ✓ should detect comparison queries
    ✓ should detect counting queries
    ✓ should detect value lookup queries
    ✓ should NOT detect semantic queries as computational
    ✓ should NOT detect greetings as computational
  ✓ isFAQQuestion
    ✓ should detect FAQ about available municipalities
    ✓ should detect FAQ about how to search
    ✓ should NOT detect ordinance queries as FAQ
  ✓ needsRAGSearch
    ✓ should return true for ordinance-related queries
    ✓ should return false for greetings
    ✓ should return false for FAQ questions
    ✓ should return false for off-topic queries
  ✓ calculateOptimalLimit
    ✓ should return high limit for listing queries with filters
    ✓ should return 1 for exact number searches with filters
    ✓ should return default limit for general queries without filters
  ✓ calculateContentLimit
    ✓ should return low limit for metadata-only queries
    ✓ should return medium limit for content queries
    ✓ should return default limit for general queries
  ✓ getOffTopicResponse
    ✓ should return weather-specific response for weather queries
    ✓ should return sports-specific response for sports queries
    ✓ should return generic response for unmatched off-topic queries

✓ src/lib/rag/__tests__/table-formatter.test.ts (20+ tests)
  ✓ formatTableForLLM
    ✓ should format table with title and context
    ✓ should include markdown table
    ✓ should include statistics for numeric columns
    ✓ should include row count and column names
    ✓ should include extraction errors if present
    ✓ should handle table without numeric columns
  ✓ formatTablesForLLM
    ✓ should format multiple tables with separators
    ✓ should return empty string for empty array
    ✓ should include instructions for LLM
  ✓ filterRelevantTables
    ✓ should filter tables by title match
    ✓ should filter tables by description match
    ✓ should filter tables by column name match
    ✓ should return all tables if query has no valid terms
    ✓ should return empty array if no tables match
    ✓ should sort tables by relevance score

Test Files  2 passed (2)
     Tests  50+ passed (50+)
  Start at  XX:XX:XX
  Duration  XXXms
```

**Si hay errores:**
- Verificar que las importaciones sean correctas
- Verificar que `vitest.config.ts` esté configurado correctamente
- Verificar que `src/test/setup.ts` exista

---

## Paso 3: Ejecutar Tests Python

```bash
cd python-cli
pytest tests/test_table_extractor.py -v
```

**Salida esperada:**
```
tests/test_table_extractor.py::test_detect_valid_table PASSED
tests/test_table_extractor.py::test_ignore_invalid_table PASSED
tests/test_table_extractor.py::test_extract_headers PASSED
tests/test_table_extractor.py::test_normalize_header PASSED
tests/test_table_extractor.py::test_parse_numeric_argentine_format PASSED
tests/test_table_extractor.py::test_parse_numeric_simple_format PASSED
tests/test_table_extractor.py::test_parse_numeric_invalid PASSED
tests/test_table_extractor.py::test_extract_rows PASSED
tests/test_table_extractor.py::test_infer_types PASSED
tests/test_table_extractor.py::test_calculate_stats PASSED
tests/test_table_extractor.py::test_generate_markdown PASSED
tests/test_table_extractor.py::test_generate_title PASSED
tests/test_table_extractor.py::test_extract_context PASSED
tests/test_table_extractor.py::test_extract_tables_with_placeholder PASSED
tests/test_table_extractor.py::test_extract_tables_multiple PASSED
tests/test_table_extractor.py::test_extract_tables_no_tables PASSED
tests/test_table_extractor.py::test_table_with_errors PASSED
tests/test_table_extractor.py::test_property_argentine_format_roundtrip PASSED
tests/test_table_extractor.py::test_property_stats_correctness PASSED
tests/test_table_extractor.py::test_property_markdown_validity PASSED
tests/test_table_extractor.py::test_property_placeholder_consistency PASSED
tests/test_table_extractor.py::test_property_json_roundtrip PASSED
tests/test_table_extractor.py::test_integration_full_extraction PASSED
tests/test_table_extractor.py::test_integration_with_scraper PASSED
tests/test_table_extractor.py::test_edge_case_empty_cells PASSED
tests/test_table_extractor.py::test_edge_case_mixed_types PASSED
tests/test_table_extractor.py::test_edge_case_special_characters PASSED
tests/test_table_extractor.py::test_edge_case_very_large_numbers PASSED
tests/test_table_extractor.py::test_edge_case_nested_tables PASSED
tests/test_table_extractor.py::test_error_handling_malformed_html PASSED
tests/test_table_extractor.py::test_error_handling_invalid_numeric PASSED
tests/test_table_extractor.py::test_error_handling_missing_context PASSED
tests/test_table_extractor.py::test_performance_large_table PASSED

============================== 33 passed in X.XXs ==============================
```

---

## Paso 4: Verificar Estructura del JSON Generado

```bash
cd python-cli
python -c "
import json
import os

# Buscar el archivo JSON más reciente de Carlos Tejedor
boletines_dir = 'boletines'
files = [f for f in os.listdir(boletines_dir) if f.startswith('carlos_tejedor') and f.endswith('.json')]

if not files:
    print('❌ No se encontraron boletines de Carlos Tejedor')
    exit(1)

# Tomar el más reciente (por nombre)
latest_file = sorted(files)[-1]
filepath = os.path.join(boletines_dir, latest_file)

print(f'📄 Analizando: {latest_file}')
print()

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)
    
    # Verificar campos básicos
    print('✅ Campos básicos:')
    print(f'  - number: {data.get(\"number\", \"N/A\")}')
    print(f'  - date: {data.get(\"date\", \"N/A\")}')
    print(f'  - municipality: {data.get(\"municipality\", \"N/A\")}')
    print()
    
    # Verificar campos nuevos
    print('✅ Campos de extracción estructurada:')
    has_text_content = 'text_content' in data
    has_tables = 'tables' in data
    print(f'  - text_content: {\"✅\" if has_text_content else \"❌\"}')
    print(f'  - tables: {\"✅\" if has_tables else \"❌\"}')
    print()
    
    # Analizar tablas
    if has_tables:
        tables = data.get('tables', [])
        print(f'📊 Tablas encontradas: {len(tables)}')
        print()
        
        if len(tables) > 0:
            for i, table in enumerate(tables, 1):
                print(f'  Tabla {i}:')
                print(f'    - ID: {table.get(\"id\", \"N/A\")}')
                print(f'    - Título: {table.get(\"title\", \"N/A\")}')
                print(f'    - Filas: {table.get(\"stats\", {}).get(\"row_count\", 0)}')
                print(f'    - Columnas: {len(table.get(\"schema\", {}).get(\"columns\", []))}')
                
                # Verificar estadísticas numéricas
                numeric_stats = table.get('stats', {}).get('numeric_stats', {})
                if numeric_stats:
                    print(f'    - Columnas numéricas: {len(numeric_stats)}')
                    for col_name, stats in numeric_stats.items():
                        print(f'      - {col_name}:')
                        print(f'        - Total: {stats.get(\"sum\", 0)}')
                        print(f'        - Máximo: {stats.get(\"max\", 0)}')
                        print(f'        - Mínimo: {stats.get(\"min\", 0)}')
                        print(f'        - Promedio: {stats.get(\"avg\", 0)}')
                
                # Verificar placeholders en text_content
                if has_text_content:
                    text_content = data.get('text_content', '')
                    placeholder = table.get('id', '')
                    if placeholder in text_content:
                        print(f'    - ✅ Placeholder [{placeholder}] encontrado en text_content')
                    else:
                        print(f'    - ❌ Placeholder [{placeholder}] NO encontrado en text_content')
                
                print()
        else:
            print('  ℹ️ No se encontraron tablas en este boletín')
    else:
        print('❌ Campo \"tables\" no encontrado en el JSON')
    
    # Verificar compatibilidad hacia atrás
    print('✅ Compatibilidad hacia atrás:')
    has_fulltext = 'fullText' in data
    print(f'  - fullText (deprecated): {\"✅\" if has_fulltext else \"❌\"}')
"
```

**Salida esperada:**
```
📄 Analizando: carlos_tejedor_105.json

✅ Campos básicos:
  - number: 105º
  - date: 08/01/2026
  - municipality: Carlos Tejedor

✅ Campos de extracción estructurada:
  - text_content: ✅
  - tables: ✅

📊 Tablas encontradas: 2

  Tabla 1:
    - ID: TABLA_1
    - Título: Escala de Tasas Municipales 2026
    - Filas: 5
    - Columnas: 3
    - Columnas numéricas: 1
      - monto_pesos:
        - Total: 15000.0
        - Máximo: 5000.0
        - Mínimo: 1500.0
        - Promedio: 3000.0
    - ✅ Placeholder [TABLA_1] encontrado en text_content

  Tabla 2:
    - ID: TABLA_2
    - Título: Horarios de Atención Municipal
    - Filas: 3
    - Columnas: 2
    - ✅ Placeholder [TABLA_2] encontrado en text_content

✅ Compatibilidad hacia atrás:
  - fullText (deprecated): ✅
```

---

## Paso 5: Probar Query Computacional en el Chatbot

### 5.1. Iniciar el servidor de desarrollo

```bash
cd chatbot
npm run dev
```

### 5.2. Abrir el navegador

Navegar a: `http://localhost:3000`

### 5.3. Abrir la consola del navegador

- Chrome/Edge: F12 → Pestaña "Console"
- Firefox: F12 → Pestaña "Consola"
- Safari: Cmd+Option+C

### 5.4. Aplicar filtros (opcional pero recomendado)

- Municipio: "Carlos Tejedor"
- Tipo: "Boletín" o "Todos"
- Fecha: Año 2026

### 5.5. Probar queries computacionales

**Query 1: Búsqueda de máximo**
```
cuál es el monto máximo de tasas municipales
```

**Logs esperados en consola:**
```
[RAG] 🧮 Query computacional detectada - incluyendo datos tabulares
[RAG] 📊 Cargando datos tabulares de documentos relevantes...
[RAG] ✅ Encontradas 2 tablas en carlos_tejedor_105.json
[RAG] 📊 Total de tablas cargadas: 2
[RAG] 🎯 Tablas relevantes filtradas: 1
[RAG] ✅ Datos tabulares agregados al contexto
```

**Respuesta esperada del LLM:**
```
Según la Escala de Tasas Municipales 2026, el monto máximo es de $5.000,00 
correspondiente a la categoría E (Comercio industrial).

Aquí está la tabla completa:

| Categoría | Descripción | Monto ($) |
|---|---|---|
| A | Comercio menor | 1.500 |
| B | Comercio mayor | 3.000 |
| C | Comercio mediano | 2.500 |
| D | Comercio grande | 4.000 |
| E | Comercio industrial | 5.000 |

**Estadísticas:**
- Total: $15.000
- Máximo: $5.000
- Mínimo: $1.500
- Promedio: $3.000
```

---

**Query 2: Suma de valores**
```
suma de todas las tasas municipales
```

**Respuesta esperada:**
```
La suma total de todas las tasas municipales es de $15.000,00.

[Tabla con desglose...]
```

---

**Query 3: Comparación**
```
diferencia entre categoría A y categoría E
```

**Respuesta esperada:**
```
La diferencia entre la categoría A ($1.500) y la categoría E ($5.000) 
es de $3.500.

[Tabla con desglose...]
```

---

**Query 4: Conteo**
```
cuántas categorías de tasas hay
```

**Respuesta esperada:**
```
Hay 5 categorías de tasas municipales (A, B, C, D, E).

[Tabla con desglose...]
```

---

### 5.6. Probar query semántica (NO computacional)

**Query:**
```
qué dice la ordenanza de tránsito
```

**Logs esperados en consola:**
```
[RAG] Query "qué dice la ordenanza de tránsito..." completada en XXXms
[RAG] Recuperados 5 documentos relevantes
```

**NO debería aparecer:**
```
[RAG] 🧮 Query computacional detectada
```

---

## Paso 6: Verificar Logs del Sistema

### Logs esperados para query computacional:

```
[ChatAPI] Nueva petición recibida
[ChatAPI] Consulta: "cuál es el monto máximo de tasas municipales"
[ChatAPI] Necesita RAG: true (isFAQ: false)
[RAG] 🧮 Query computacional detectada - incluyendo datos tabulares
[RAG] Después de filtros: 10 documentos
[RAG] Documentos cargados para BM25: 10
[RAG] Índice BM25 construido con 10 docs
[RAG] 🎯 LÍMITE SOLICITADO: 5 documentos
[RAG] BM25 top 5 resultados: [...]
[RAG] ✅ Devolviendo 5 documentos al LLM
[RAG] 📊 Cargando datos tabulares de documentos relevantes...
[RAG] ✅ Encontradas 2 tablas en carlos_tejedor_105.json
[RAG] 📊 Total de tablas cargadas: 2
[RAG] 🎯 Tablas relevantes filtradas: 1
[RAG] ✅ Datos tabulares agregados al contexto
[RAG] Query "cuál es el monto máximo..." completada en XXXms
[RAG] Recuperados 5 documentos relevantes
[RAG] Incluidas 1 tablas estructuradas
[ChatAPI] Usando modelo premium para búsqueda: anthropic/claude-3.5-sonnet
```

---

## Checklist de Validación Final

### Python (Backend)
- [ ] ✅ 33 tests de `test_table_extractor.py` pasando
- [ ] ✅ JSON generado tiene campo `text_content`
- [ ] ✅ JSON generado tiene campo `tables` (array)
- [ ] ✅ Tablas tienen estructura correcta (id, title, schema, data, stats, markdown)
- [ ] ✅ Placeholders `[TABLA_N]` presentes en `text_content`
- [ ] ✅ Estadísticas numéricas calculadas correctamente
- [ ] ✅ Campo `fullText` presente (compatibilidad hacia atrás)

### TypeScript (Frontend)
- [ ] ✅ Dependencias de testing instaladas
- [ ] ✅ 50+ tests pasando (query-classifier + table-formatter)
- [ ] ✅ Query computacional detectada correctamente
- [ ] ✅ Logs de carga de tablas aparecen en consola
- [ ] ✅ Tablas filtradas por relevancia
- [ ] ✅ Tablas formateadas con Markdown + estadísticas
- [ ] ✅ LLM responde con cálculos correctos
- [ ] ✅ Respuesta incluye tabla Markdown como referencia
- [ ] ✅ Query semántica NO activa carga de tablas

### Integración End-to-End
- [ ] ✅ Scraper genera JSON con tablas estructuradas
- [ ] ✅ Chatbot carga tablas desde JSON
- [ ] ✅ Chatbot detecta queries computacionales
- [ ] ✅ Chatbot incluye datos tabulares en contexto
- [ ] ✅ LLM puede realizar cálculos sobre datos reales
- [ ] ✅ Usuario recibe respuestas precisas con tablas

---

## Troubleshooting

### Error: "Cannot find module 'vitest'"

**Solución:**
```bash
cd chatbot
npm install --save-dev vitest @vitest/ui @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom
```

### Error: "No se encontraron boletines de Carlos Tejedor"

**Solución:**
```bash
cd python-cli
python sibom_scraper.py --municipality "Carlos Tejedor" --limit 1
```

### Error: Tests TypeScript fallan con "Cannot find module '@/lib/types'"

**Solución:**
Verificar que `vitest.config.ts` tenga el alias configurado:
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

### Error: "Query computacional no detectada"

**Verificar:**
1. Que la query contenga palabras clave computacionales (suma, máximo, comparar, etc.)
2. Que `isComputationalQuery()` esté importada correctamente en `retriever.ts`
3. Que los logs estén habilitados (NODE_ENV !== 'production')

### Error: "No se cargan tablas desde JSON"

**Verificar:**
1. Que el JSON tenga el campo `tables` (array)
2. Que las tablas tengan la estructura correcta
3. Que `readFileContent()` esté funcionando correctamente
4. Que el cache no esté sirviendo un JSON antiguo (invalidar cache)

---

## Conclusión

Si todos los checkpoints pasan, la implementación de extracción de datos tabulares está completa y funcionando correctamente. El sistema ahora puede:

1. ✅ Extraer tablas HTML preservando estructura semántica
2. ✅ Calcular estadísticas numéricas automáticamente
3. ✅ Detectar queries computacionales del usuario
4. ✅ Cargar y filtrar tablas relevantes
5. ✅ Formatear tablas para consumo del LLM
6. ✅ Permitir al LLM realizar cálculos sobre datos reales
7. ✅ Responder con precisión a preguntas computacionales

**¡Felicitaciones! 🎉**
