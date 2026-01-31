#!/usr/bin/env python3
"""
utils/sqlite_manager.py

Manejo centralizado de SQLite para normativas.
Separa metadata ligera del contenido pesado para optimizar consultas.

@version 3.0.0
@created 2026-01-29
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()


# ============================================================================
# ESQUEMA DE LA BASE DE DATOS
# ============================================================================

SCHEMA = """
-- Tabla principal (metadata ligera - para búsquedas rápidas)
CREATE TABLE IF NOT EXISTS normativas (
    id TEXT PRIMARY KEY,
    municipality TEXT NOT NULL,
    type TEXT NOT NULL,
    number TEXT NOT NULL,
    year TEXT NOT NULL,
    date TEXT,
    title TEXT,
    source_bulletin TEXT NOT NULL,
    source_bulletin_url TEXT,
    norma_url TEXT,
    doc_index INTEGER,
    status TEXT DEFAULT 'vigente',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de contenido (pesado - separada para consultas selectivas)
CREATE TABLE IF NOT EXISTS normativa_content (
    id TEXT PRIMARY KEY REFERENCES normativas(id) ON DELETE CASCADE,
    content TEXT,
    tablas_md TEXT,
    montos_json TEXT
);

-- Tabla para documentos de transparencia (balances, presupuestos, etc.)
CREATE TABLE IF NOT EXISTS transparency_docs (
    id TEXT PRIMARY KEY,
    municipio TEXT NOT NULL,
    tipo_documento TEXT NOT NULL,
    periodo TEXT,
    fecha_documento TEXT,
    url_origen TEXT NOT NULL,
    titulo_extraido TEXT,
    status TEXT DEFAULT 'completed',
    pdf_file TEXT,
    calidad_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de contenido para documentos de transparencia
CREATE TABLE IF NOT EXISTS transparency_content (
    id TEXT PRIMARY KEY REFERENCES transparency_docs(id) ON DELETE CASCADE,
    tablas_md TEXT,  -- JSON array de tablas en Markdown
    full_text TEXT   -- Texto completo extraído
);

-- Índices para búsquedas eficientes (normativas)
CREATE INDEX IF NOT EXISTS idx_mun_type_year ON normativas(municipality, type, year);
CREATE INDEX IF NOT EXISTS idx_mun_year ON normativas(municipality, year);
CREATE INDEX IF NOT EXISTS idx_type_year ON normativas(type, year);
CREATE INDEX IF NOT EXISTS idx_date ON normativas(date);

-- Índices para documentos de transparencia
CREATE INDEX IF NOT EXISTS idx_trans_mun_tipo ON transparency_docs(municipio, tipo_documento);
CREATE INDEX IF NOT EXISTS idx_trans_periodo ON transparency_docs(periodo);
CREATE INDEX IF NOT EXISTS idx_trans_mun ON transparency_docs(municipio);

-- Vista para búsqueda completa (incluye contenido)
CREATE VIEW IF NOT EXISTS normativas_full AS
SELECT
    n.*,
    c.content,
    c.tablas_md,
    c.montos_json
FROM normativas n
LEFT JOIN normativa_content c ON n.id = c.id;

-- Vista resumida (sin contenido pesado)
CREATE VIEW IF NOT EXISTS normativas_summary AS
SELECT
    id, municipality, type, number, year, date, title,
    source_bulletin, norma_url, status
FROM normativas;

-- Vista completa para documentos de transparencia
CREATE VIEW IF NOT EXISTS transparency_full AS
SELECT
    t.*,
    tc.tablas_md,
    tc.full_text
FROM transparency_docs t
LEFT JOIN transparency_content tc ON t.id = tc.id;
"""


# ============================================================================
# SQLITE MANAGER
# ============================================================================

class SQLiteManager:
    """
    Maneja operaciones de SQLite para normativas.

    Características:
    - Separa metadata de contenido pesado
    - Índices optimizados para búsquedas
    - Soporta upsert (INSERT OR REPLACE)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: Ruta a la base de datos. Default: data/normativas.db
        """
        from config import DEFAULT_DB_PATH

        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos con el esquema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def insert_normativas(
        self,
        normativas: List[Any],
        show_progress: bool = False
    ) -> int:
        """
        Inserta o actualiza normativas en la base de datos.

        Separa automáticamente el contenido pesado.

        Args:
            normativas: Lista de objetos Normativa (con to_dict())
            show_progress: Mostrar progreso en consola

        Returns:
            Número de normativas insertadas/actualizadas
        """
        if not normativas:
            return 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for i, n in enumerate(normativas):
                # Convertir a dict si es dataclass
                if hasattr(n, 'to_dict'):
                    data = n.to_dict()
                    municipio = data.get('municipality', '')
                    content = data.get('content', '')
                    tablas_md = data.get('tablas_md', [])
                    montos = data.get('montos_extraidos', [])
                else:
                    data = n
                    municipio = data.get('municipality', '')
                    content = data.get('content', '')
                    tablas_md = data.get('tablas_md', [])
                    montos = data.get('montos_extraidos', [])

                # Insertar metadata principal
                cursor.execute("""
                    INSERT OR REPLACE INTO normativas
                    (id, municipality, type, number, year, date, title,
                     source_bulletin, source_bulletin_url, norma_url,
                     doc_index, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('id'),
                    municipio,
                    data.get('type'),
                    data.get('number'),
                    data.get('year'),
                    data.get('date'),
                    data.get('title'),
                    data.get('source_bulletin'),
                    data.get('source_bulletin_url', ''),
                    data.get('norma_url', ''),
                    data.get('doc_index', 0),
                    data.get('status', 'vigente')
                ))

                # Insertar contenido solo si existe
                if content or tablas_md:
                    cursor.execute("""
                        INSERT OR REPLACE INTO normativa_content
                        (id, content, tablas_md, montos_json)
                        VALUES (?, ?, ?, ?)
                    """, (
                        data.get('id'),
                        content,
                        json.dumps(tablas_md, ensure_ascii=False),
                        json.dumps(montos, ensure_ascii=False)
                    ))

                if show_progress and (i + 1) % 100 == 0:
                    console.print(f"[dim]  Progreso: {i + 1}/{len(normativas)}[/dim]")

            conn.commit()

        return len(normativas)

    def get_normativa(self, normativa_id: str, include_content: bool = True) -> Optional[Dict]:
        """
        Obtiene una normativa por ID.

        Args:
            normativa_id: ID de la normativa
            include_content: Incluir contenido completo

        Returns:
            Diccionario con la normativa o None
        """
        table = "normativas_full" if include_content else "normativas"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (normativa_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def search(
        self,
        municipality: Optional[str] = None,
        tipo: Optional[str] = None,
        year: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca normativas con filtros.

        Args:
            municipality: Filtro por municipio
            tipo: Filtro por tipo
            year: Filtro por año
            limit: Límite de resultados

        Returns:
            Lista de normativas (sin contenido pesado)
        """
        query = "SELECT * FROM normativas_summary WHERE 1=1"
        params = []

        if municipality:
            query += " AND municipality = ?"
            params.append(municipality)

        if tipo:
            query += " AND type = ?"
            params.append(tipo)

        if year:
            query += " AND year = ?"
            params.append(year)

        query += f" ORDER BY date DESC LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la base de datos.

        Returns:
            Diccionario con estadísticas (incluye transparency)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total de normativas
            cursor.execute("SELECT COUNT(*) FROM normativas")
            total = cursor.fetchone()[0]

            # Por municipio
            cursor.execute("""
                SELECT municipality, COUNT(*) as count
                FROM normativas
                GROUP BY municipality
                ORDER BY count DESC
            """)
            by_municipality = dict(cursor.fetchall())

            # Por tipo
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM normativas
                GROUP BY type
                ORDER BY count DESC
            """)
            by_type = dict(cursor.fetchall())

            # Por año
            cursor.execute("""
                SELECT year, COUNT(*) as count
                FROM normativas
                GROUP BY year
                ORDER BY year DESC
            """)
            by_year = dict(cursor.fetchall())

            # Con contenido
            cursor.execute("SELECT COUNT(*) FROM normativa_content")
            with_content = cursor.fetchone()[0]

            # Estadísticas de transparency
            trans_stats = self.get_transparency_stats()

            return {
                "total_normativas": total,
                "with_content": with_content,
                "by_municipality": by_municipality,
                "by_type": by_type,
                "by_year": by_year,
                "db_path": str(self.db_path),
                # Transparency stats
                "total_transparency": trans_stats["total_docs"],
                "transparency_by_municipality": trans_stats["by_municipality"],
                "transparency_by_type": trans_stats["by_type"],
                "transparency_with_tables": trans_stats["with_tables"]
            }

    def print_stats(self):
        """Imprime estadísticas en formato tabla."""
        stats = self.get_stats()

        from rich.table import Table

        # Tabla de normativas
        table = Table(title="Estadísticas de Normativas")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor")

        table.add_row("Total de normativas", f"{stats['total_normativas']:,}")
        table.add_row("Con contenido", f"{stats['with_content']:,}")
        table.add_row("Municipios", f"{len(stats['by_municipality'])}")
        table.add_row("Tipos", f"{len(stats['by_type'])}")
        table.add_row("Años", f"{len(stats['by_year'])}")

        console.print(table)

        # Tabla de transparencia
        if stats.get('total_transparency', 0) > 0:
            trans_table = Table(title="Documentos de Transparencia")
            trans_table.add_column("Métrica", style="green")
            trans_table.add_column("Valor")

            trans_table.add_row("Total documentos", f"{stats['total_transparency']:,}")
            trans_table.add_row("Con tablas", f"{stats['transparency_with_tables']:,}")
            trans_table.add_row("Municipios", f"{len(stats['transparency_by_municipality'])}")
            trans_table.add_row("Tipos", f"{len(stats['transparency_by_type'])}")

            console.print(trans_table)

        # Top 5 municipios
        if stats['by_municipality']:
            console.print("\n[bold]Top 5 Municipios (Normativas):[/bold]")
            for mun, count in list(stats['by_municipality'].items())[:5]:
                console.print(f"  {mun}: {count:,}")

        if stats.get('transparency_by_municipality'):
            console.print("\n[bold]Top 5 Municipios (Transparencia):[/bold]")
            for mun, count in list(stats['transparency_by_municipality'].items())[:5]:
                console.print(f"  {mun}: {count:,}")

    def export_json(self, output_path: Path, include_content: bool = False):
        """
        Exporta todas las normativas a JSON.

        Args:
            output_path: Ruta del archivo JSON de salida
            include_content: Incluir contenido completo (puede ser muy grande)
        """
        table = "normativas_full" if include_content else "normativas_summary"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

        data = [dict(row) for row in rows]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Exportadas {len(data)} normativas a {output_path}[/green]")

    # ==========================================================================
    # DOCUMENTOS DE TRANSPARENCIA
    # ==========================================================================

    def insert_transparency_doc(self, doc_data: Dict[str, Any]) -> str:
        """
        Inserta o actualiza un documento de transparencia.

        Args:
            doc_data: Diccionario con los datos del documento
                - id: ID único (obligatorio)
                - municipio: Nombre del municipio
                - tipo_documento: Tipo (balances, presupuestos, etc.)
                - periodo: Período (ej: "2021-T1")
                - fecha_documento: Fecha del documento
                - url_origen: URL de origen
                - titulo_extraido: Título extraído
                - tablas_md: Lista de tablas en Markdown
                - calidad: Metadata de calidad
                - pdf_file: Ruta al PDF (opcional)
                - json_file: Nombre del archivo JSON (para que el chatbot lo encuentre)
                - status: Estado (default: "completed")

        Returns:
            ID del documento insertado
        """
        doc_id = doc_data.get('id', self._generate_transparency_id(doc_data))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insertar metadata
            cursor.execute("""
                INSERT OR REPLACE INTO transparency_docs
                (id, municipio, tipo_documento, periodo, fecha_documento,
                 url_origen, titulo_extraido, status, pdf_file, json_file, calidad_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                doc_data.get('municipio', ''),
                doc_data.get('tipo_documento', ''),
                doc_data.get('periodo', ''),
                doc_data.get('fecha_documento', ''),
                doc_data.get('url_origen', ''),
                doc_data.get('titulo_extraido', ''),
                doc_data.get('status', 'completed'),
                doc_data.get('pdf_file'),
                doc_data.get('json_file'),  # Nombre del archivo JSON
                json.dumps(doc_data.get('calidad', {}), ensure_ascii=False)
            ))

            # Insertar contenido (tablas)
            tablas_md = doc_data.get('tablas_md', [])
            if tablas_md:
                cursor.execute("""
                    INSERT OR REPLACE INTO transparency_content
                    (id, tablas_md, full_text)
                    VALUES (?, ?, ?)
                """, (
                    doc_id,
                    json.dumps(tablas_md, ensure_ascii=False),
                    doc_data.get('titulo_extraido', '')
                ))

            conn.commit()

        return doc_id

    def _generate_transparency_id(self, doc_data: Dict[str, Any]) -> str:
        """Genera un ID único para un documento de transparencia."""
        import hashlib
        municipio = doc_data.get('municipio', 'unknown').replace(' ', '_')
        tipo = doc_data.get('tipo_documento', 'doc')
        url = doc_data.get('url_origen', '')
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"TRANS_{municipio}_{tipo}_{hash_suffix}"

    def get_transparency_docs(
        self,
        municipio: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        periodo: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Busca documentos de transparencia con filtros.

        Args:
            municipio: Filtro por municipio
            tipo_documento: Filtro por tipo (balances, presupuestos, etc.)
            periodo: Filtro por período
            limit: Límite de resultados

        Returns:
            Lista de documentos
        """
        query = "SELECT * FROM transparency_full WHERE 1=1"
        params = []

        if municipio:
            query += " AND municipio = ?"
            params.append(municipio)

        if tipo_documento:
            query += " AND tipo_documento = ?"
            params.append(tipo_documento)

        if periodo:
            query += " AND periodo LIKE ?"
            params.append(f"%{periodo}%")

        query += f" ORDER BY created_at DESC LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_transparency_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de documentos de transparencia."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total
            cursor.execute("SELECT COUNT(*) FROM transparency_docs")
            total = cursor.fetchone()[0]

            # Por municipio
            cursor.execute("""
                SELECT municipio, COUNT(*) as count
                FROM transparency_docs
                GROUP BY municipio
                ORDER BY count DESC
            """)
            by_municipality = dict(cursor.fetchall())

            # Por tipo
            cursor.execute("""
                SELECT tipo_documento, COUNT(*) as count
                FROM transparency_docs
                GROUP BY tipo_documento
                ORDER BY count DESC
            """)
            by_type = dict(cursor.fetchall())

            # Por período
            cursor.execute("""
                SELECT periodo, COUNT(*) as count
                FROM transparency_docs
                WHERE periodo != ''
                GROUP BY periodo
                ORDER BY periodo DESC
            """)
            by_period = dict(cursor.fetchall())

            # Con tablas
            cursor.execute("SELECT COUNT(*) FROM transparency_content")
            with_tables = cursor.fetchone()[0]

            return {
                "total_docs": total,
                "with_tables": with_tables,
                "by_municipality": by_municipality,
                "by_type": by_type,
                "by_period": by_period
            }

    def get_all_transparency_for_index(self) -> List[Dict]:
        """
        Retorna todos los documentos de transparencia en formato
        compatible con el índice del chatbot.

        Usa el campo json_file guardado para que el chatbot pueda cargar el contenido.

        Returns:
            Lista de documentos en formato NormativaIndexEntry
        """
        query = """
        SELECT id, municipio, tipo_documento, periodo, url_origen,
               titulo_extraido, json_file, created_at
        FROM transparency_docs
        ORDER BY created_at DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        # Convertir al formato esperado por el chatbot
        # La estructura del chatbot espera:
        # {id, m (municipality), t (type), n (number), y (year), d (date), ti (title), sb (source), url}
        result = []
        for row in rows:
            # Convertir Row a dict para acceso seguro
            row_dict = dict(row)

            # Extraer año del período
            periodo = row_dict.get('periodo', '') or ''
            year_match = periodo.split('-')[0] if periodo else 's/d'

            municipio = row_dict.get('municipio', '')
            tipo = row_dict.get('tipo_documento', '')

            # Usar el json_file guardado, o generar uno si no existe
            json_file = row_dict.get('json_file')
            if json_file:
                sb = json_file.replace('.json', '')  # Quitar extensión
            else:
                # Fallback: buscar archivo o usar nombre genérico
                from config import BOLETINES_DIR
                municipio_dir = BOLETINES_DIR / municipio.replace(' ', '_')
                if municipio_dir.exists():
                    import glob
                    pattern = f"{municipio.replace(' ', '_')}_{tipo.capitalize()}_*.json"
                    matching_files = list(municipio_dir.glob(pattern))
                    if matching_files:
                        sb = sorted(matching_files, key=lambda p: p.stat().st_mtime, reverse=True)[0].stem
                    else:
                        sb = f"{municipio.replace(' ', '_')}_{tipo}"
                else:
                    sb = f"{municipio.replace(' ', '_')}_{tipo}"

            result.append({
                'id': row_dict.get('id', ''),
                'm': municipio,
                't': tipo,  # balances, presupuestos, etc.
                'n': '0',  # Los documentos de transparencia no tienen número
                'y': year_match,
                'd': periodo or 's/d',
                'ti': (row_dict.get('titulo_extraido', '') or '')[:100],  # Truncar a 100 chars
                'sb': sb,  # Nombre del archivo JSON (sin extensión) para que el chatbot lo encuentre
                'url': row_dict.get('url_origen', '')
            })

        return result


# ============================================================================
# FUNCIONES DE CONVENIENCIA (compatibilidad con v1/v2)
# ============================================================================

def create_database(db_path: str) -> sqlite3.Connection:
    """Crea la base de datos con el esquema (compatibilidad)."""
    manager = SQLiteManager(Path(db_path))
    return sqlite3.connect(manager.db_path)


def insert_normativa(conn: sqlite3.Connection, normativa: Dict[str, Any]) -> None:
    """Inserta una normativa (compatibilidad con código antiguo)."""
    manager = SQLiteManager(Path(conn.execute("PRAGMA database_list").fetchone()[1]))
    manager.insert_normativas([normativa])


def migrate_from_json(
    json_path: str,
    db_path: str = "data/normativas.db",
    batch_size: int = 1000
) -> None:
    """
    Migra datos desde un JSON de normativas a SQLite.

    Args:
        json_path: Ruta al archivo JSON (normativas_index.json o _compact)
        db_path: Ruta de la base de datos SQLite
        batch_size: Tamaño del lote para commits
    """
    json_file = Path(json_path)
    if not json_file.exists():
        raise FileNotFoundError(f"No existe: {json_path}")

    print(f"📂 Leyendo JSON: {json_path}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    normativas = data.get('normativas', data)

    print(f"📊 Total normativas: {len(normativas):,}")

    manager = SQLiteManager(Path(db_path))
    manager.insert_normativas(normativas, show_progress=True)

    stats = manager.get_stats()
    print(f"\n✅ Migración completada")
    print(f"   Total en BD: {stats['total_normativas']:,}")


def query_normativas(
    db_path: str,
    municipality: Optional[str] = None,
    type_: Optional[str] = None,
    year: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Ejecuta una consulta en la BD (compatibilidad)."""
    manager = SQLiteManager(Path(db_path))
    return manager.search(
        municipality=municipality,
        tipo=type_,
        year=year,
        limit=limit
    )


def print_stats(db_path: str) -> None:
    """Imprime estadísticas de la BD (compatibilidad)."""
    manager = SQLiteManager(Path(db_path))
    manager.print_stats()


def get_sqlite_manager(db_path: Optional[Path] = None) -> SQLiteManager:
    """
    Retorna una instancia del SQLiteManager.

    Args:
        db_path: Ruta opcional a la base de datos

    Returns:
        Instancia de SQLiteManager
    """
    return SQLiteManager(db_path)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="SQLite Manager v3.0")
    parser.add_argument('--db', default='data/normativas.db', help='Ruta a la BD')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')
    parser.add_argument('--export', help='Exportar a JSON')
    parser.add_argument('--content', action='store_true', help='Incluir contenido en exportación')

    args = parser.parse_args()

    mgr = SQLiteManager(Path(args.db))

    if args.stats:
        mgr.print_stats()

    if args.export:
        mgr.export_json(Path(args.export), include_content=args.content)


if __name__ == "__main__":
    main()
