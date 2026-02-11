# Requirements Document

## Introduction

Este documento define los requisitos para implementar la extracción y procesamiento de datos tabulares en el scraper de SIBOM. El objetivo es preservar la estructura semántica de las tablas HTML para que puedan ser recuperadas y analizadas computacionalmente por el sistema RAG, permitiendo responder preguntas que requieran cálculos, comparaciones y agregaciones sobre datos numéricos.

## Glossary

- **Scraper**: Componente Python CLI que extrae contenido de boletines oficiales de SIBOM
- **Table_Extractor**: Módulo que identifica y extrae tablas HTML preservando su estructura
- **Structured_Data**: Representación JSON de una tabla con schema, datos tipados y metadatos
- **RAG_System**: Sistema de Retrieval-Augmented Generation del chatbot
- **Query_Router**: Componente que determina si una consulta requiere búsqueda semántica o computacional
- **Computational_Query**: Consulta que requiere operaciones numéricas (suma, máximo, comparación)

## Requirements

### Requirement 1: Detección de Tablas HTML

**User Story:** Como scraper, quiero detectar todas las tablas HTML en el contenido de un boletín, para poder extraerlas y procesarlas de forma estructurada.

#### Acceptance Criteria

1. WHEN el Scraper procesa contenido HTML, THE Table_Extractor SHALL identificar todos los elementos `<table>` presentes
2. WHEN una tabla es detectada, THE Table_Extractor SHALL extraer el contexto circundante (texto anterior y posterior, máximo 500 caracteres cada uno)
3. WHEN una tabla no tiene contenido válido (menos de 2 filas o 2 columnas), THE Table_Extractor SHALL ignorarla y continuar con el procesamiento
4. IF el HTML contiene tablas anidadas, THEN THE Table_Extractor SHALL procesar solo la tabla más interna

### Requirement 2: Extracción de Estructura Tabular

**User Story:** Como sistema de datos, quiero que las tablas se extraigan con su estructura completa (headers, filas, tipos de datos), para poder realizar operaciones computacionales sobre ellas.

#### Acceptance Criteria

1. WHEN una tabla es extraída, THE Table_Extractor SHALL identificar la fila de headers (primera fila con `<th>` o primera `<tr>`)
2. WHEN se extraen los datos, THE Table_Extractor SHALL crear un array de objetos donde cada objeto representa una fila con keys correspondientes a los headers
3. WHEN un valor de celda contiene un número, THE Table_Extractor SHALL convertirlo a tipo numérico (int o float)
4. WHEN un valor numérico tiene formato argentino (1.500,00), THE Table_Extractor SHALL parsearlo correctamente removiendo puntos de miles y convirtiendo coma a punto decimal
5. WHEN una celda está vacía, THE Table_Extractor SHALL representarla como null en el JSON
6. WHEN los headers contienen caracteres especiales o espacios, THE Table_Extractor SHALL normalizarlos a snake_case para las keys del JSON

### Requirement 3: Generación de Metadatos de Tabla

**User Story:** Como sistema RAG, quiero que cada tabla tenga metadatos descriptivos, para poder encontrar tablas relevantes mediante búsqueda semántica.

#### Acceptance Criteria

1. WHEN una tabla es procesada, THE Table_Extractor SHALL generar un título descriptivo basado en el contexto circundante
2. WHEN una tabla es procesada, THE Table_Extractor SHALL generar una descripción en lenguaje natural que explique qué contiene la tabla
3. WHEN una tabla tiene columnas numéricas, THE Table_Extractor SHALL calcular estadísticas básicas (sum, max, min, avg, count)
4. WHEN una tabla es procesada, THE Table_Extractor SHALL generar una representación Markdown para visualización en el chat
5. WHEN una tabla es procesada, THE Table_Extractor SHALL registrar el schema con nombres de columnas y tipos de datos inferidos

### Requirement 4: Integración con Documento JSON

**User Story:** Como pipeline de datos, quiero que las tablas estructuradas se integren en el JSON del boletín manteniendo la relación con el texto, para tener un único archivo por boletín.

#### Acceptance Criteria

1. WHEN el Scraper genera el JSON de un boletín, THE Scraper SHALL incluir un array `tables` con todas las tablas estructuradas
2. WHEN una tabla es extraída del texto, THE Scraper SHALL reemplazarla con un placeholder `[TABLA_N]` en el campo `text_content`
3. WHEN se genera el JSON, THE Scraper SHALL incluir la posición del placeholder en el texto para cada tabla
4. WHEN un boletín no tiene tablas, THE Scraper SHALL establecer `tables` como array vacío y `metadata.has_tables` como false
5. THE Scraper SHALL mantener compatibilidad con el formato JSON existente agregando los nuevos campos sin modificar los existentes

### Requirement 5: Serialización y Deserialización

**User Story:** Como desarrollador, quiero que los datos tabulares se serialicen y deserialicen correctamente, para garantizar la integridad de los datos.

#### Acceptance Criteria

1. FOR ALL tablas válidas, serializar a JSON y deserializar SHALL producir datos equivalentes (round-trip)
2. WHEN se serializa una tabla, THE Table_Extractor SHALL usar `ensure_ascii=False` para preservar caracteres especiales
3. WHEN se deserializa una tabla, THE Table_Extractor SHALL restaurar los tipos numéricos correctamente
4. IF el JSON de una tabla es inválido, THEN THE Table_Extractor SHALL registrar el error y continuar sin la tabla

### Requirement 6: Soporte para Queries Computacionales en RAG

**User Story:** Como usuario del chatbot, quiero poder hacer preguntas que requieran cálculos sobre datos tabulares, para obtener respuestas precisas basadas en los datos reales.

#### Acceptance Criteria

1. WHEN el Query_Router recibe una consulta con patrones computacionales (suma, máximo, comparar, cuántos), THE Query_Router SHALL identificarla como Computational_Query
2. WHEN una Computational_Query es detectada, THE RAG_System SHALL incluir los datos estructurados de tablas relevantes en el contexto
3. WHEN el LLM recibe datos tabulares estructurados, THE RAG_System SHALL formatearlos de manera que el LLM pueda realizar cálculos
4. WHEN se responde una Computational_Query, THE RAG_System SHALL incluir la tabla Markdown en la respuesta para que el usuario vea los datos fuente

### Requirement 7: Manejo de Errores en Extracción de Tablas

**User Story:** Como sistema robusto, quiero manejar errores en la extracción de tablas sin interrumpir el procesamiento del boletín completo.

#### Acceptance Criteria

1. IF una tabla tiene estructura malformada, THEN THE Table_Extractor SHALL registrar un warning y continuar con el texto plano
2. IF la conversión de un valor numérico falla, THEN THE Table_Extractor SHALL mantener el valor como string
3. IF el contexto circundante no puede extraerse, THEN THE Table_Extractor SHALL usar "Tabla sin contexto" como título
4. WHEN ocurre un error en una tabla, THE Table_Extractor SHALL incluir el error en el campo `extraction_errors` del JSON
