"""
Chunker inteligente para documentos SIBOM.

Estrategia:
- Balances: Genera chunks de RESUMEN con totales clave
- Normativas: Chunks semánticos por sección (artículos, considerandos)
- Tablas: Preserva estructura completa o agrupa por categorías
"""

from typing import List, Dict, Any, Tuple
import re
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentChunk:
    """Representa un chunk de documento con metadata."""

    chunk_id: str
    chunk_text: str
    chunk_type: str  # 'summary', 'table', 'article', 'narrative'
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a dict para Qdrant."""
        return {
            'chunk_id': self.chunk_id,
            'chunk_text': self.chunk_text,
            'chunk_type': self.chunk_type,
            **self.metadata
        }


class IntelligentChunker:
    """Chunker que entiende la estructura semántica de documentos."""

    # Tamaños de chunk (en caracteres, aprox 4 chars = 1 token)
    MAX_CHUNK_SIZE = 4096  # ~1024 tokens
    MIN_CHUNK_SIZE = 512   # ~128 tokens
    OVERLAP_SIZE = 200     # ~50 tokens

    def chunk_balance(self, balance_data: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Genera chunks inteligentes para documentos de balance.

        Estrategia:
        1. Chunk de RESUMEN EJECUTIVO (totales clave)
        2. Chunks por CATEGORÍA PRINCIPAL (si hay múltiples tablas)
        3. NO genera chunks por fila individual
        """
        chunks = []
        municipio = balance_data.get('municipio', 'Desconocido')
        periodo = balance_data.get('periodo', '')
        tipo_detalle = balance_data.get('tipo_detalle', 'Balance')
        doc_id = f"{municipio}_{balance_data.get('tipo_documento', 'balance')}_{periodo}".replace(
            ' ', '_')

        # Base metadata común
        base_metadata = {
            'source_type': 'transparency',
            'municipality': municipio,
            'document_type': balance_data.get('tipo_documento', 'balances'),
            'period': periodo,
            'year': self._extract_year(periodo),
            'url': balance_data.get('url_origen', ''),
            'document_id': doc_id,
            # Metadata en espanol para compatibilidad con RAG
            'municipio': municipio,
            'tipo_documento': balance_data.get('tipo_documento', 'balances'),
            'tipo_detalle': tipo_detalle,
            'periodo': periodo,
            'fecha_documento': balance_data.get('fecha_documento')
        }

        # 1. CHUNK DE RESUMEN EJECUTIVO
        summary_chunk = self._create_summary_chunk(
            balance_data, doc_id, base_metadata)
        if summary_chunk:
            chunks.append(summary_chunk)

        # 2. CHUNKS POR TABLA (preservando estructura)
        table_chunks = self._create_table_chunks(
            balance_data, doc_id, base_metadata)
        chunks.extend(table_chunks)

        # 3. CHUNK DE CONTENIDO NARRATIVO (deshabilitado para balances - redundante con tablas)
        # narrative_chunk = self._create_narrative_chunk(
        #     balance_data, doc_id, base_metadata)
        # if narrative_chunk:
        #     chunks.append(narrative_chunk)

        return chunks

    def _create_summary_chunk(
        self,
        balance_data: Dict[str, Any],
        doc_id: str,
        base_metadata: Dict[str, Any]
    ) -> DocumentChunk | None:
        """
        Genera chunk de RESUMEN EJECUTIVO con números clave.

        Este chunk responde preguntas tipo:
        - "¿Cuáles son los números clave del balance?"
        - "¿Cuánto fueron los ingresos totales?"
        - "¿Cuál fue el resultado del periodo?"
        """
        tablas_md = balance_data.get('tablas_md', [])
        if not tablas_md:
            return None

        # Extraer totales de las tablas
        totales = self._extract_totals_from_tables(tablas_md)
        if not totales:
            return None

        # Construir texto de resumen estructurado
        cabecera = balance_data.get('cabecera', {})
        tipo_detalle = balance_data.get('tipo_detalle', 'Balance')
        periodo = balance_data.get('periodo', '')
        municipio = balance_data.get('municipio', 'Desconocido')

        summary_lines = [
            f"# RESUMEN EJECUTIVO - {tipo_detalle}",
            f"**Municipio:** {municipio}",
            f"**Periodo:** {periodo}",
        ]

        # Agregar info de cabecera si existe
        if cabecera:
            if 'ejercicio' in cabecera:
                summary_lines.append(f"**Ejercicio:** {cabecera['ejercicio']}")
            if 'periodo_inicio' in cabecera and 'periodo_fin' in cabecera:
                summary_lines.append(
                    f"**Rango de fechas:** {cabecera['periodo_inicio']} a {cabecera['periodo_fin']}"
                )

        summary_lines.append("\n## CIFRAS CLAVE\n")

        # Agregar totales encontrados
        for categoria, valor in totales.items():
            summary_lines.append(f"**{categoria}:** {valor}")

        # Calcular resultado si hay ingresos y egresos
        if 'Total Recursos' in totales and 'Total Gastos' in totales:
            try:
                recursos_num = self._parse_currency(totales['Total Recursos'])
                gastos_num = self._parse_currency(totales['Total Gastos'])
                resultado = recursos_num - gastos_num
                resultado_str = self._format_currency(resultado)
                summary_lines.append(
                    f"**Resultado (Superávit/Déficit):** {resultado_str}")
            except:
                pass

        summary_text = "\n".join(summary_lines)

        return DocumentChunk(
            chunk_id=f"{doc_id}_summary",
            chunk_text=summary_text,
            chunk_type='summary',
            metadata={
                **base_metadata,
                'is_executive_summary': True,
                'contains_key_numbers': True
            }
        )

    def _extract_totals_from_tables(self, tablas_md: List[str]) -> Dict[str, str]:
        """
        Extrae filas de TOTALES de tablas markdown.

        Maneja formatos variados:
        | **Total de Recursos:** |  | **9.362.683.953,23** |  |
        |  | Total de Gastos: |  | 499.982.355,90 |
        | **Total Disponibilidades:** | | **469.581.055,31** | **469.581.055,31** |

        Busca keywords en CUALQUIER columna y extrae valores después.
        """
        totales = {}

        # Palabras clave para categorías importantes (sin dos puntos)
        exact_keywords = {
            'total de recursos': 'Total Recursos',
            'total recursos': 'Total Recursos',
            'recursos percibidos': 'Total Recursos',
            'total de gastos': 'Total Gastos',
            'total gastos': 'Total Gastos',
            'gastos devengados': 'Total Gastos',
            'total gastos presupuestarios': 'Total Gastos',
            'saldo final': 'Saldo Final',
            'total disponibilidades': 'Total Disponibilidades'
        }

        for tabla in tablas_md:
            for line in tabla.split('\n'):
                # Ignorar headers y separadores markdown
                if line.startswith('|---') or line.startswith('| ---') or not line.strip():
                    continue

                # NO filtrar columnas vacías para mantener posiciones correctas
                raw_cols = line.split('|')
                columns = [col.strip() for col in raw_cols]

                if len(columns) < 3:
                    continue

                # Buscar keyword en CUALQUIER columna
                matched_key = None
                keyword_col_idx = -1

                for col_idx, col_text in enumerate(columns):
                    if not col_text:  # Columna vacía, skip
                        continue

                    # Limpiar asteriscos y dos puntos
                    categoria_raw = col_text.replace('**', '').strip()
                    categoria_clean = categoria_raw.rstrip(':').lower()

                    # Ignorar códigos contables (números de 6+ dígitos)
                    if re.match(r'^\d{6,}$', categoria_raw):
                        continue

                    # Verificar si coincide con keyword
                    for keyword, canonical_name in exact_keywords.items():
                        if keyword in categoria_clean:
                            matched_key = canonical_name
                            keyword_col_idx = col_idx
                            break

                    if matched_key:
                        break

                if matched_key and keyword_col_idx >= 0:
                    # Buscar valor en columnas DESPUÉS del keyword
                    for val_idx in range(keyword_col_idx + 1, len(columns)):
                        valor_col = columns[val_idx].replace('**', '').strip()

                        if not valor_col:  # Columna vacía
                            continue

                        # Extraer número (formato argentino: 9.362.683.953,23)
                        valor_match = re.search(r'\$?\s*([\d.,]+)', valor_col)

                        if valor_match:
                            valor = valor_match.group(1)

                            # Validar formato argentino: puntos miles + coma decimal
                            if ',' in valor and (valor.count('.') >= 2 or len(valor) > 10):
                                try:
                                    num_value = float(valor.replace(
                                        '.', '').replace(',', '.'))
                                    if num_value > 10000:  # Ignorar valores pequeños
                                        totales[matched_key] = f"${valor}"
                                        break
                                except ValueError:
                                    continue

        return totales

    def _extract_category_name(self, line: str) -> str | None:
        """Extrae el nombre de la categoría de una línea de tabla."""
        # Formato típico: | Categoría | Valor |
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 2:
            return parts[0]
        return None

    def _normalize_category_name(self, name: str) -> str:
        """Normaliza nombres de categorías a formato estándar."""
        name_lower = name.lower()

        if 'recurso' in name_lower or 'ingreso' in name_lower or 'percibido' in name_lower:
            return 'Total Recursos'
        elif 'gasto' in name_lower or 'egreso' in name_lower or 'devengado' in name_lower:
            return 'Total Gastos'
        elif 'saldo' in name_lower:
            return 'Saldo Final'
        elif 'resultado' in name_lower:
            return 'Resultado'
        else:
            return name.title()

    def _parse_currency(self, currency_str: str) -> float:
        """Convierte string de moneda a float."""
        # Remover símbolo $, espacios, y convertir comas a puntos
        clean = currency_str.replace('$', '').replace(
            ' ', '').replace('.', '').replace(',', '.')
        return float(clean)

    def _format_currency(self, amount: float) -> str:
        """Formatea número a string de moneda."""
        # Formato argentino: $ 1.234.567,89
        formatted = f"${amount:,.2f}"
        # Convertir punto a coma decimal y coma a punto miles
        formatted = formatted.replace(',', 'TEMP').replace(
            '.', ',').replace('TEMP', '.')
        return formatted

    def _create_table_chunks(
        self,
        balance_data: Dict[str, Any],
        doc_id: str,
        base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        Genera chunks preservando tablas completas (si caben) o por secciones.

        NO genera chunks por fila individual.
        """
        chunks = []
        tablas_md = balance_data.get('tablas_md', [])

        for idx, tabla in enumerate(tablas_md):
            # Si la tabla es pequeña, mantenerla completa
            if len(tabla) <= self.MAX_CHUNK_SIZE:
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_table_{idx}",
                    chunk_text=tabla,
                    chunk_type='table',
                    metadata={
                        **base_metadata,
                        'table_index': idx,
                        'is_complete_table': True
                    }
                )
                chunks.append(chunk)
            else:
                # Tabla grande: dividir por secciones lógicas
                # (implementar si es necesario)
                pass

        return chunks

    def _create_narrative_chunk(
        self,
        balance_data: Dict[str, Any],
        doc_id: str,
        base_metadata: Dict[str, Any]
    ) -> DocumentChunk | None:
        """Genera chunk con contenido narrativo (si existe)."""
        contenido = balance_data.get('contenido', '').strip()

        # Ignorar si es solo repetición de tablas
        if not contenido or len(contenido) < self.MIN_CHUNK_SIZE:
            return None

        # Verificar que no sea solo texto de "tabla extraída"
        if contenido.lower().startswith('tabla extraída') or contenido.lower().startswith('# tabla'):
            return None

        return DocumentChunk(
            chunk_id=f"{doc_id}_narrative",
            chunk_text=contenido,
            chunk_type='narrative',
            metadata={
                **base_metadata,
                'contains_narrative': True
            }
        )

    def chunk_normativa(self, normativa_data: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Genera chunks para normativas (ordenanzas, decretos, resoluciones).

        Estrategia:
        - Preservar artículos completos cuando sea posible
        - Separar considerandos como chunk independiente
        - Respetar estructura semántica del documento
        """
        chunks = []

        municipio = normativa_data.get('municipality', 'Desconocido')
        tipo = normativa_data.get('type', 'normativa')
        numero = normativa_data.get('number', '')
        año = normativa_data.get('year', 0)

        doc_id = f"{municipio}_{tipo}_{numero}_{año}".replace(
            ' ', '_').replace('/', '_')

        base_metadata = {
            'source_type': 'normativa',
            'municipality': municipio,
            'document_type': tipo,
            'number': numero,
            'year': año,
            'url': normativa_data.get('url', ''),
            'title': normativa_data.get('title', ''),
            'document_id': doc_id
        }

        full_text = normativa_data.get('fullText', '')

        if not full_text:
            return chunks

        # Estrategia simple: dividir por artículos
        articulos = self._split_by_articles(full_text)

        if articulos:
            # Hay estructura de artículos
            for idx, articulo in enumerate(articulos):
                if len(articulo.strip()) < 50:  # Ignorar artículos vacíos
                    continue

                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_art_{idx}",
                    chunk_text=articulo,
                    chunk_type='article',
                    metadata={
                        **base_metadata,
                        'article_number': idx + 1
                    }
                )
                chunks.append(chunk)
        else:
            # Sin estructura clara: chunking por tamaño con overlap
            text_chunks = self._chunk_by_size(full_text)
            for idx, text_chunk in enumerate(text_chunks):
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_chunk_{idx}",
                    chunk_text=text_chunk,
                    chunk_type='text',
                    metadata={
                        **base_metadata,
                        'chunk_index': idx
                    }
                )
                chunks.append(chunk)

        return chunks

    def _split_by_articles(self, text: str) -> List[str]:
        """
        Divide texto por artículos.

        Detecta patrones: "ARTÍCULO 1°", "Art. 2", "Artículo 3.-"
        """
        # Pattern para detectar inicio de artículos
        article_pattern = r'(?:ARTÍCULO|Artículo|Art\.?)\s*\d+[°º]?'

        matches = list(re.finditer(article_pattern, text, re.IGNORECASE))

        if len(matches) < 2:
            # No hay suficiente estructura de artículos
            return []

        articulos = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            articulo_text = text[start:end].strip()
            articulos.append(articulo_text)

        return articulos

    def _chunk_by_size(self, text: str, max_size: int | None = None) -> List[str]:
        """
        Divide texto por tamaño con overlap.

        Intenta cortar en límites de oraciones cuando es posible.
        """
        if max_size is None:
            max_size = self.MAX_CHUNK_SIZE

        if len(text) <= max_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + max_size

            if end >= len(text):
                # Último chunk
                chunks.append(text[start:].strip())
                break

            # Intentar cortar en fin de oración
            chunk_text = text[start:end]
            last_period = max(
                chunk_text.rfind('. '),
                chunk_text.rfind('.\n'),
                chunk_text.rfind('?\n'),
                chunk_text.rfind('!\n')
            )

            if last_period > max_size * 0.5:  # Si hay un punto en la segunda mitad
                end = start + last_period + 1

            chunks.append(text[start:end].strip())
            start = end - self.OVERLAP_SIZE  # Overlap para contexto

        return chunks

    def _extract_year(self, periodo: str) -> int:
        """Extrae año de un string de periodo."""
        # Formato típico: "2024-T1" o "2024"
        match = re.search(r'(\d{4})', periodo)
        if match:
            return int(match.group(1))
        return 0

    def chunk_document(self, doc_data: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Punto de entrada principal: detecta tipo de documento y aplica estrategia.
        """
        # Detectar tipo de documento
        if 'tipo_documento' in doc_data:
            # Es documento de transparencia
            tipo = doc_data['tipo_documento']
            if tipo == 'balances':
                return self.chunk_balance(doc_data)
            # Agregar más tipos si es necesario
        elif 'type' in doc_data and doc_data['type'] in ['ordenanza', 'decreto', 'resolucion']:
            # Es normativa
            return self.chunk_normativa(doc_data)

        # Fallback: chunking genérico
        return []


# Funciones de conveniencia
def chunk_balance_file(filepath: Path) -> List[DocumentChunk]:
    """Procesa un archivo de balance JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunker = IntelligentChunker()
    return chunker.chunk_balance(data)


def chunk_normativa_file(filepath: Path) -> List[DocumentChunk]:
    """Procesa un archivo de normativa JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunker = IntelligentChunker()
    return chunker.chunk_normativa(data)


if __name__ == '__main__':
    # Test básico
    import sys

    if len(sys.argv) < 2:
        print("Uso: python chunker.py <archivo.json>")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"Error: {filepath} no existe")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunker = IntelligentChunker()
    chunks = chunker.chunk_document(data)

    print(f"\n✅ Generados {len(chunks)} chunks\n")

    for chunk in chunks[:3]:  # Mostrar primeros 3
        print(f"ID: {chunk.chunk_id}")
        print(f"Tipo: {chunk.chunk_type}")
        print(f"Texto ({len(chunk.chunk_text)} chars):")
        print(chunk.chunk_text[:300] + "...\n")
